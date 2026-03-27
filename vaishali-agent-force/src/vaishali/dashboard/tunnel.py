"""Remote access tunnel management for Vaishali Agent Force dashboard.

Provides support for:
  - Cloudflare Quick Tunnel (no account needed — started via ./vaf.sh tunnel)
  - ngrok (quick temporary fallback)

URL detection strategy (in order):
  1. VAF_TUNNEL_URL env var  — set manually in .env for a permanent URL
  2. .tunnel_url file         — written by `./vaf.sh tunnel` when quick tunnel starts
  3. ngrok local API          — http://localhost:4040/api/tunnels fallback
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

# Written by `./vaf.sh tunnel` when a quick tunnel URL is captured from cloudflared output
_TUNNEL_URL_FILE = Path(settings.base_dir) / ".tunnel_url"


def get_tunnel_url() -> str | None:
    """Get the active tunnel URL for remote dashboard access.

    Returns:
        The tunnel URL (e.g. https://abc-123.trycloudflare.com) or None.
    """
    # 1. Explicit override in .env — highest priority
    env_url = os.getenv("VAF_TUNNEL_URL", "").strip()
    if env_url:
        return env_url

    # 2. File written by `./vaf.sh tunnel` (quick tunnel auto-detection)
    url = _read_tunnel_url_file()
    if url:
        return url

    # 3. ngrok local API fallback
    url = _get_ngrok_tunnel_url()
    if url:
        return url

    return None


def _read_tunnel_url_file() -> str | None:
    """Read the quick-tunnel URL saved by `./vaf.sh tunnel`.

    vaf.sh parses cloudflared's stdout and writes the trycloudflare.com URL
    to PROJECT_DIR/.tunnel_url.  File is deleted when tunnel stops.
    """
    try:
        if _TUNNEL_URL_FILE.exists():
            url = _TUNNEL_URL_FILE.read_text().strip()
            if url.startswith("https://"):
                return url
    except OSError:
        pass
    return None


def _get_cloudflared_tunnel_url() -> str | None:
    """Legacy: probe named cloudflared tunnel (requires cert.pem/account).

    Kept for backwards compatibility but not called by default — quick tunnel
    via _read_tunnel_url_file() is preferred.
    """
    try:
        result = subprocess.run(
            ["cloudflared", "tunnel", "info", "vaishali-agentforce", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        url = data.get("url") or data.get("publicUrl")
        if url:
            return url
    except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired, Exception):
        pass

    return None


def _get_ngrok_tunnel_url() -> str | None:
    """Try to get ngrok tunnel URL from local API.

    ngrok exposes tunnels on http://localhost:4040/api/tunnels
    """
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:4040/api/tunnels"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            tunnels = data.get("tunnels", [])
            # Find the first HTTP tunnel
            for tunnel in tunnels:
                if tunnel.get("proto") == "http":
                    return tunnel.get("public_url")
    except (json.JSONDecodeError, subprocess.TimeoutExpired, Exception):
        pass

    return None


def start_ngrok_tunnel(port: int = 3000) -> str | None:
    """Start an ngrok tunnel to the given port.

    Launches ngrok as a background subprocess.

    Args:
        port: Local port to tunnel (default 3000 for React dashboard)

    Returns:
        The ngrok public URL or None if ngrok is not installed or fails.
    """
    try:
        # Check if ngrok is installed
        result = subprocess.run(
            ["which", "ngrok"],
            capture_output=True,
            timeout=2,
        )
        if result.returncode != 0:
            log.warning("ngrok not installed. Install with: brew install ngrok")
            return None

        # Start ngrok in background
        subprocess.Popen(
            ["ngrok", "http", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # Wait a moment for ngrok to start and expose the API
        import time
        time.sleep(2)

        # Get the public URL from ngrok API
        return _get_ngrok_tunnel_url()

    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        log.error(f"Failed to start ngrok: {e}")
        return None


def tunnel_status() -> dict[str, Any]:
    """Get the current tunnel status.

    Returns:
        {
            "provider": "cloudflare" | "ngrok" | None,
            "url": "https://..." or None,
            "active": True | False,
            "local_port": 3000,
        }
    """
    url = get_tunnel_url()

    status = {
        "provider": None,
        "url": url,
        "active": url is not None,
        "local_port": 3000,
    }

    if url:
        if "trycloudflare.com" in url or "cloudflare" in url.lower():
            status["provider"] = "cloudflare"
        elif "ngrok" in url.lower():
            status["provider"] = "ngrok"

    return status

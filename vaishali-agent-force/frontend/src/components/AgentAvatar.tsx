/**
 * AgentAvatar — Animated SVG mascots for each agent arm.
 *
 * Finance  = Calm Owl       (green)
 * Content  = Playful Fox    (purple)
 * Education= Nerdy Cat      (blue)
 * Health   = Coach Panda    (orange)
 *
 * Each character has 4 visual states: idle, success, warning, running.
 * CSS keyframe animations drive breathing, celebration, and alert pulses.
 */
import React, { useEffect, useRef } from 'react';
import { colors } from '../theme/colors';

export type AgentId = 'finance' | 'content' | 'education' | 'health';
export type AgentState = 'idle' | 'success' | 'warning' | 'running';

interface AgentAvatarProps {
  agent: AgentId;
  state?: AgentState;
  size?: number;
  showLabel?: boolean;
}

/* ── Agent metadata ──────────────────────────────────────────── */

const AGENT_CONFIG: Record<AgentId, {
  name: string;
  character: string;
  colour: string;
  glow: string;
}> = {
  finance:   { name: 'Owlbert',  character: 'owl',   colour: colors.accent.finance,   glow: '#4ade8040' },
  content:   { name: 'Foxy',     character: 'fox',   colour: colors.accent.content,   glow: '#a78bfa40' },
  education: { name: 'Whiskers', character: 'cat',   colour: colors.accent.education, glow: '#60a5fa40' },
  health:    { name: 'Bamboo',   character: 'panda', colour: colors.accent.health,    glow: '#fb923c40' },
};

/* ── Inject global CSS keyframes once ───────────────────────── */

let _stylesInjected = false;

function injectAnimations() {
  if (_stylesInjected) return;
  _stylesInjected = true;
  const style = document.createElement('style');
  style.textContent = `
    @keyframes vaf-breathe {
      0%, 100% { transform: scaleY(1); }
      50%      { transform: scaleY(1.04); }
    }
    @keyframes vaf-bounce {
      0%, 100% { transform: translateY(0); }
      30%      { transform: translateY(-6px); }
      50%      { transform: translateY(-3px); }
      70%      { transform: translateY(-5px); }
    }
    @keyframes vaf-pulse {
      0%, 100% { opacity: 1; }
      50%      { opacity: 0.6; }
    }
    @keyframes vaf-spin {
      0%   { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    @keyframes vaf-wiggle {
      0%, 100% { transform: rotate(0deg); }
      25%      { transform: rotate(-5deg); }
      75%      { transform: rotate(5deg); }
    }
    @keyframes vaf-confetti-pop {
      0%   { opacity: 0; transform: scale(0) translateY(0); }
      40%  { opacity: 1; transform: scale(1.2) translateY(-8px); }
      100% { opacity: 0; transform: scale(0.6) translateY(-20px); }
    }
  `;
  document.head.appendChild(style);
}

/* ── State → animation mapping ──────────────────────────────── */

function stateAnimation(state: AgentState): React.CSSProperties {
  switch (state) {
    case 'idle':
      return { animation: 'vaf-breathe 3s ease-in-out infinite' };
    case 'success':
      return { animation: 'vaf-bounce 0.8s ease-in-out 3' };
    case 'warning':
      return { animation: 'vaf-wiggle 0.5s ease-in-out infinite' };
    case 'running':
      return { animation: 'vaf-pulse 1.2s ease-in-out infinite' };
  }
}

/* ── SVG Character Renderers ─────────────────────────────────── */

function OwlSvg({ colour, state, size }: { colour: string; state: AgentState; size: number }) {
  const eyeOpen = state !== 'running';
  return (
    <svg viewBox="0 0 100 100" width={size} height={size}>
      {/* Body */}
      <ellipse cx="50" cy="60" rx="30" ry="28" fill={colour} opacity={0.2} />
      <ellipse cx="50" cy="58" rx="26" ry="24" fill={colour} opacity={0.35} />
      {/* Head */}
      <circle cx="50" cy="38" r="22" fill={colour} opacity={0.5} />
      {/* Ear tufts */}
      <polygon points="33,22 28,8 38,20" fill={colour} opacity={0.6} />
      <polygon points="67,22 72,8 62,20" fill={colour} opacity={0.6} />
      {/* Eye circles */}
      <circle cx="40" cy="36" r="9" fill="#0f1117" />
      <circle cx="60" cy="36" r="9" fill="#0f1117" />
      <circle cx="40" cy="36" r="7" fill="#1c2333" />
      <circle cx="60" cy="36" r="7" fill="#1c2333" />
      {/* Pupils */}
      {eyeOpen ? (
        <>
          <circle cx="42" cy="35" r="3.5" fill={colour} />
          <circle cx="62" cy="35" r="3.5" fill={colour} />
          <circle cx="43" cy="34" r="1.2" fill="#fff" />
          <circle cx="63" cy="34" r="1.2" fill="#fff" />
        </>
      ) : (
        <>
          <line x1="34" y1="36" x2="46" y2="36" stroke={colour} strokeWidth="2" strokeLinecap="round" />
          <line x1="54" y1="36" x2="66" y2="36" stroke={colour} strokeWidth="2" strokeLinecap="round" />
        </>
      )}
      {/* Beak */}
      <polygon points="47,42 53,42 50,48" fill="#fbbf24" />
      {/* Belly detail */}
      <ellipse cx="50" cy="64" rx="14" ry="12" fill={colour} opacity={0.15} />
      {/* Feet */}
      <ellipse cx="40" cy="84" rx="8" ry="3" fill={colour} opacity={0.4} />
      <ellipse cx="60" cy="84" rx="8" ry="3" fill={colour} opacity={0.4} />
      {/* Glasses for "calm wise" look */}
      <circle cx="40" cy="36" r="10" fill="none" stroke={colour} strokeWidth="1.2" opacity={0.4} />
      <circle cx="60" cy="36" r="10" fill="none" stroke={colour} strokeWidth="1.2" opacity={0.4} />
      <line x1="50" y1="36" x2="50" y2="36" stroke={colour} strokeWidth="1" opacity={0.3} />
      {/* Warning exclamation */}
      {state === 'warning' && (
        <text x="78" y="18" fontSize="16" fill="#fbbf24" fontWeight="bold">!</text>
      )}
      {/* Success stars */}
      {state === 'success' && (
        <>
          <text x="12" y="14" fontSize="10" fill="#fbbf24" style={{ animation: 'vaf-confetti-pop 1s ease-out forwards' }}>★</text>
          <text x="76" y="10" fontSize="8" fill={colour} style={{ animation: 'vaf-confetti-pop 1.2s ease-out 0.2s forwards' }}>★</text>
          <text x="20" y="8" fontSize="7" fill="#fff" style={{ animation: 'vaf-confetti-pop 1s ease-out 0.4s forwards' }}>✦</text>
        </>
      )}
    </svg>
  );
}

function FoxSvg({ colour, state, size }: { colour: string; state: AgentState; size: number }) {
  return (
    <svg viewBox="0 0 100 100" width={size} height={size}>
      {/* Tail */}
      <path d="M 72 70 Q 90 50 85 35 Q 82 42 78 45 Q 80 55 72 65" fill={colour} opacity={0.35} />
      {/* Body */}
      <ellipse cx="48" cy="65" rx="24" ry="20" fill={colour} opacity={0.25} />
      {/* Head */}
      <ellipse cx="48" cy="40" rx="20" ry="18" fill={colour} opacity={0.45} />
      {/* Ears */}
      <polygon points="32,28 24,8 38,22" fill={colour} opacity={0.55} />
      <polygon points="64,28 72,8 58,22" fill={colour} opacity={0.55} />
      {/* Inner ears */}
      <polygon points="33,26 27,12 37,23" fill="#ff9edb" opacity={0.3} />
      <polygon points="63,26 69,12 59,23" fill="#ff9edb" opacity={0.3} />
      {/* Face mask */}
      <ellipse cx="48" cy="44" rx="12" ry="10" fill={colour} opacity={0.15} />
      {/* Eyes */}
      <ellipse cx="40" cy="38" rx="4" ry={state === 'success' ? 1.5 : 4.5} fill="#0f1117" />
      <ellipse cx="56" cy="38" rx="4" ry={state === 'success' ? 1.5 : 4.5} fill="#0f1117" />
      {state !== 'success' && (
        <>
          <circle cx="41" cy="37" r="2" fill={colour} />
          <circle cx="57" cy="37" r="2" fill={colour} />
          <circle cx="42" cy="36" r="0.8" fill="#fff" />
          <circle cx="58" cy="36" r="0.8" fill="#fff" />
        </>
      )}
      {/* Nose */}
      <ellipse cx="48" cy="44" rx="3" ry="2" fill="#1c2333" />
      {/* Mouth — playful smirk */}
      <path d="M 44 47 Q 48 51 52 47" fill="none" stroke="#1c2333" strokeWidth="1.2" strokeLinecap="round" />
      {/* Whiskers */}
      <line x1="30" y1="42" x2="38" y2="43" stroke={colour} strokeWidth="0.8" opacity={0.4} />
      <line x1="30" y1="46" x2="38" y2="45" stroke={colour} strokeWidth="0.8" opacity={0.4} />
      <line x1="58" y1="43" x2="66" y2="42" stroke={colour} strokeWidth="0.8" opacity={0.4} />
      <line x1="58" y1="45" x2="66" y2="46" stroke={colour} strokeWidth="0.8" opacity={0.4} />
      {/* Paws */}
      <ellipse cx="36" cy="82" rx="7" ry="4" fill={colour} opacity={0.35} />
      <ellipse cx="60" cy="82" rx="7" ry="4" fill={colour} opacity={0.35} />
      {/* Belly */}
      <ellipse cx="48" cy="68" rx="10" ry="10" fill={colour} opacity={0.12} />
      {/* Pen in paw — content creator! */}
      <line x1="62" y1="72" x2="72" y2="58" stroke={colour} strokeWidth="2" strokeLinecap="round" opacity={0.5} />
      <circle cx="72" cy="57" r="1.5" fill="#fbbf24" />
      {/* State indicators */}
      {state === 'warning' && (
        <text x="76" y="18" fontSize="16" fill="#fbbf24" fontWeight="bold">!</text>
      )}
      {state === 'success' && (
        <>
          <text x="10" y="14" fontSize="10" fill="#fbbf24" style={{ animation: 'vaf-confetti-pop 1s ease-out forwards' }}>★</text>
          <text x="74" y="12" fontSize="8" fill={colour} style={{ animation: 'vaf-confetti-pop 1.2s ease-out 0.2s forwards' }}>★</text>
        </>
      )}
    </svg>
  );
}

function CatSvg({ colour, state, size }: { colour: string; state: AgentState; size: number }) {
  return (
    <svg viewBox="0 0 100 100" width={size} height={size}>
      {/* Tail */}
      <path d="M 68 72 Q 85 60 88 42 Q 86 50 82 55" fill="none" stroke={colour} strokeWidth="4" strokeLinecap="round" opacity={0.4} />
      {/* Body */}
      <ellipse cx="48" cy="66" rx="22" ry="18" fill={colour} opacity={0.22} />
      {/* Head */}
      <circle cx="48" cy="40" r="20" fill={colour} opacity={0.4} />
      {/* Ears — pointy cat ears */}
      <polygon points="32,26 22,4 40,22" fill={colour} opacity={0.5} />
      <polygon points="64,26 74,4 56,22" fill={colour} opacity={0.5} />
      <polygon points="33,24 26,10 39,22" fill="#ff9edb" opacity={0.2} />
      <polygon points="63,24 70,10 57,22" fill="#ff9edb" opacity={0.2} />
      {/* Glasses — nerdy! */}
      <rect x="30" y="33" width="14" height="10" rx="3" fill="none" stroke={colour} strokeWidth="1.5" opacity={0.7} />
      <rect x="52" y="33" width="14" height="10" rx="3" fill="none" stroke={colour} strokeWidth="1.5" opacity={0.7} />
      <line x1="44" y1="38" x2="52" y2="38" stroke={colour} strokeWidth="1" opacity={0.5} />
      {/* Eyes behind glasses */}
      <ellipse cx="37" cy="38" rx="3" ry={state === 'success' ? 1 : 3.5} fill="#0f1117" />
      <ellipse cx="59" cy="38" rx="3" ry={state === 'success' ? 1 : 3.5} fill="#0f1117" />
      {state !== 'success' && (
        <>
          <circle cx="38" cy="37" r="1.8" fill={colour} />
          <circle cx="60" cy="37" r="1.8" fill={colour} />
          <circle cx="39" cy="36.5" r="0.7" fill="#fff" />
          <circle cx="61" cy="36.5" r="0.7" fill="#fff" />
        </>
      )}
      {/* Nose */}
      <polygon points="46,44 50,44 48,47" fill="#ff9edb" opacity={0.6} />
      {/* Mouth */}
      <path d="M 44 48 Q 48 51 52 48" fill="none" stroke="#1c2333" strokeWidth="1" strokeLinecap="round" />
      {/* Whiskers */}
      <line x1="26" y1="44" x2="36" y2="45" stroke={colour} strokeWidth="0.7" opacity={0.35} />
      <line x1="26" y1="48" x2="36" y2="47" stroke={colour} strokeWidth="0.7" opacity={0.35} />
      <line x1="60" y1="45" x2="70" y2="44" stroke={colour} strokeWidth="0.7" opacity={0.35} />
      <line x1="60" y1="47" x2="70" y2="48" stroke={colour} strokeWidth="0.7" opacity={0.35} />
      {/* Book — because nerdy */}
      <rect x="22" y="70" width="14" height="10" rx="1" fill={colour} opacity={0.3} />
      <line x1="29" y1="70" x2="29" y2="80" stroke={colour} strokeWidth="1" opacity={0.5} />
      {/* Paws */}
      <ellipse cx="38" cy="82" rx="6" ry="3.5" fill={colour} opacity={0.3} />
      <ellipse cx="58" cy="82" rx="6" ry="3.5" fill={colour} opacity={0.3} />
      {/* State indicators */}
      {state === 'warning' && (
        <text x="76" y="18" fontSize="16" fill="#fbbf24" fontWeight="bold">!</text>
      )}
      {state === 'success' && (
        <>
          <text x="8" y="12" fontSize="10" fill="#fbbf24" style={{ animation: 'vaf-confetti-pop 1s ease-out forwards' }}>★</text>
          <text x="76" y="10" fontSize="8" fill={colour} style={{ animation: 'vaf-confetti-pop 1.2s ease-out 0.2s forwards' }}>★</text>
        </>
      )}
    </svg>
  );
}

function PandaSvg({ colour, state, size }: { colour: string; state: AgentState; size: number }) {
  return (
    <svg viewBox="0 0 100 100" width={size} height={size}>
      {/* Body */}
      <ellipse cx="50" cy="66" rx="26" ry="22" fill={colour} opacity={0.2} />
      {/* Head */}
      <circle cx="50" cy="40" r="22" fill={colour} opacity={0.15} />
      <circle cx="50" cy="40" r="22" fill="#e2e8f0" opacity={0.3} />
      {/* Ears */}
      <circle cx="32" cy="22" r="8" fill="#1c2333" opacity={0.8} />
      <circle cx="68" cy="22" r="8" fill="#1c2333" opacity={0.8} />
      <circle cx="32" cy="22" r="5" fill={colour} opacity={0.3} />
      <circle cx="68" cy="22" r="5" fill={colour} opacity={0.3} />
      {/* Eye patches — classic panda */}
      <ellipse cx="38" cy="38" rx="8" ry="7" fill="#1c2333" opacity={0.85} />
      <ellipse cx="62" cy="38" rx="8" ry="7" fill="#1c2333" opacity={0.85} />
      {/* Eyes */}
      <ellipse cx="38" cy="38" rx="3.5" ry={state === 'success' ? 1 : 3.5} fill="#e2e8f0" />
      <ellipse cx="62" cy="38" rx="3.5" ry={state === 'success' ? 1 : 3.5} fill="#e2e8f0" />
      {state !== 'success' && (
        <>
          <circle cx="39" cy="37" r="2" fill={colour} />
          <circle cx="63" cy="37" r="2" fill={colour} />
          <circle cx="40" cy="36.5" r="0.8" fill="#fff" />
          <circle cx="64" cy="36.5" r="0.8" fill="#fff" />
        </>
      )}
      {/* Nose */}
      <ellipse cx="50" cy="45" rx="4" ry="2.5" fill="#1c2333" />
      {/* Mouth */}
      <path d="M 46 48 Q 50 52 54 48" fill="none" stroke="#1c2333" strokeWidth="1.2" strokeLinecap="round" />
      {/* Belly badge */}
      <ellipse cx="50" cy="68" rx="14" ry="12" fill="#e2e8f0" opacity={0.15} />
      {/* Arms — coach pose */}
      <ellipse cx="28" cy="60" rx="6" ry="10" fill="#1c2333" opacity={0.5} transform="rotate(-15 28 60)" />
      <ellipse cx="72" cy="60" rx="6" ry="10" fill="#1c2333" opacity={0.5} transform="rotate(15 72 60)" />
      {/* Dumbbell for coach vibe */}
      <line x1="14" y1="54" x2="26" y2="54" stroke={colour} strokeWidth="2.5" strokeLinecap="round" opacity={0.5} />
      <circle cx="14" cy="54" r="3.5" fill={colour} opacity={0.4} />
      <circle cx="26" cy="54" r="3.5" fill={colour} opacity={0.4} />
      {/* Feet */}
      <ellipse cx="40" cy="84" rx="8" ry="4" fill="#1c2333" opacity={0.5} />
      <ellipse cx="60" cy="84" rx="8" ry="4" fill="#1c2333" opacity={0.5} />
      {/* Headband — coach style */}
      <path d="M 30 30 Q 50 24 70 30" fill="none" stroke={colour} strokeWidth="2.5" strokeLinecap="round" opacity={0.6} />
      {/* State indicators */}
      {state === 'warning' && (
        <text x="78" y="18" fontSize="16" fill="#fbbf24" fontWeight="bold">!</text>
      )}
      {state === 'success' && (
        <>
          <text x="10" y="10" fontSize="10" fill="#fbbf24" style={{ animation: 'vaf-confetti-pop 1s ease-out forwards' }}>★</text>
          <text x="78" y="8" fontSize="8" fill={colour} style={{ animation: 'vaf-confetti-pop 1.2s ease-out 0.2s forwards' }}>★</text>
        </>
      )}
    </svg>
  );
}

/* ── Character dispatch ──────────────────────────────────────── */

const CHARACTER_MAP: Record<string, React.FC<{ colour: string; state: AgentState; size: number }>> = {
  owl:   OwlSvg,
  fox:   FoxSvg,
  cat:   CatSvg,
  panda: PandaSvg,
};

/* ── Main Component ──────────────────────────────────────────── */

export function AgentAvatar({ agent, state = 'idle', size = 64, showLabel = false }: AgentAvatarProps) {
  const mountedRef = useRef(false);

  useEffect(() => {
    if (!mountedRef.current) {
      injectAnimations();
      mountedRef.current = true;
    }
  }, []);

  const config = AGENT_CONFIG[agent];
  const CharacterSvg = CHARACTER_MAP[config.character];

  return (
    <div style={{
      display: 'inline-flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 4,
    }}>
      {/* Glow backdrop */}
      <div style={{
        position: 'relative',
        width: size,
        height: size,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${config.glow} 0%, transparent 70%)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        ...stateAnimation(state),
        transformOrigin: 'center bottom',
      }}>
        <CharacterSvg colour={config.colour} state={state} size={size * 0.85} />

        {/* Status dot */}
        <div style={{
          position: 'absolute',
          bottom: 2,
          right: 2,
          width: size * 0.18,
          height: size * 0.18,
          borderRadius: '50%',
          backgroundColor: statusDotColour(state),
          border: `2px solid ${colors.bg.secondary}`,
          boxSizing: 'border-box',
        }} />
      </div>

      {showLabel && (
        <span style={{
          fontSize: 10,
          color: config.colour,
          fontWeight: 500,
          letterSpacing: '0.02em',
          textAlign: 'center',
          lineHeight: 1,
        }}>
          {config.name}
        </span>
      )}
    </div>
  );
}

function statusDotColour(state: AgentState): string {
  switch (state) {
    case 'idle':    return colors.text.muted;
    case 'success': return colors.status.success;
    case 'warning': return colors.status.warning;
    case 'running': return colors.accent.teal;
  }
}

/* ── Helper: derive AgentState from summary data ─────────────── */

export function deriveAgentState(agent: AgentId, data: any): AgentState {
  if (!data) return 'idle';

  switch (agent) {
    case 'finance': {
      if (data.anomalies?.length > 0) {
        const hasHigh = data.anomalies.some((a: any) => a.severity === 'high');
        return hasHigh ? 'warning' : 'success';
      }
      return data.total_balance_gbp != null ? 'success' : 'idle';
    }
    case 'content': {
      if (data.drafts_waiting_review?.length > 0) return 'warning';
      if (data.top_ideas?.length > 0) return 'success';
      return 'idle';
    }
    case 'education': {
      if ((data.items_processed ?? 0) > 0) return 'success';
      return 'idle';
    }
    case 'health': {
      if (data.body_score == null) return 'idle';
      if (data.body_score < 5) return 'warning';
      return 'success';
    }
  }
}

export { AGENT_CONFIG };

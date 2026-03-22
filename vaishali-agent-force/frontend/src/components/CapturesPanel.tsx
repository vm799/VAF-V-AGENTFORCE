import React, { useEffect, useState, useCallback } from 'react';
import { colors } from '../theme/colors';

// Gold accent not in core theme — defined locally
const GOLD = '#c9a84c';
const TEAL = colors.accent.teal;

interface Capture {
  id: number;
  created_at: string;
  agent: string;
  title: string;
  content: string;
  source_url?: string;
  vault_path: string;
  revenue_angle: string;
  obsidian_written: number;
}

const AGENT_META: Record<string, { emoji: string; color: string; bg: string }> = {
  SENTINEL: { emoji: '🎖️', color: '#c9a84c', bg: 'rgba(201,168,76,0.12)' },
  FORGE:    { emoji: '🏗️', color: '#2dd4bf', bg: 'rgba(45,212,191,0.12)' },
  AMPLIFY:  { emoji: '📱', color: '#a78bfa', bg: 'rgba(167,139,250,0.12)' },
  PHOENIX:  { emoji: '💰', color: '#fb923c', bg: 'rgba(251,146,60,0.12)' },
  VITALITY: { emoji: '⚡', color: '#4ade80', bg: 'rgba(74,222,128,0.12)' },
  CIPHER:   { emoji: '🔍', color: '#60a5fa', bg: 'rgba(96,165,250,0.12)' },
  AEGIS:    { emoji: '🛡️', color: '#f87171', bg: 'rgba(248,113,113,0.12)' },
  NEXUS:    { emoji: '🔮', color: '#e879f9', bg: 'rgba(232,121,249,0.12)' },
};

const DEFAULT_AGENT_META = { emoji: '📎', color: '#888', bg: 'rgba(136,136,136,0.12)' };

function agentMeta(agent: string) {
  return AGENT_META[agent.toUpperCase()] ?? DEFAULT_AGENT_META;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)  return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)  return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function CapturesPanel() {
  const [captures, setCaptures] = useState<Capture[]>([]);
  const [byAgent, setByAgent]   = useState<Record<string, number>>({});
  const [total, setTotal]       = useState(0);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [filter, setFilter]     = useState<string>('ALL');
  const [loading, setLoading]   = useState(true);

  const load = useCallback(async () => {
    try {
      const res = await fetch('/api/captures?limit=50');
      if (!res.ok) return;
      const data = await res.json();
      setCaptures(data.captures ?? []);
      setByAgent(data.by_agent ?? {});
      setTotal(data.total ?? 0);
    } catch (_) {
      // API not yet running
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const iv = setInterval(load, 30_000);
    const onFocus = () => load();
    window.addEventListener('focus', onFocus);
    return () => { clearInterval(iv); window.removeEventListener('focus', onFocus); };
  }, [load]);

  const filtered = filter === 'ALL'
    ? captures
    : captures.filter(c => c.agent.toUpperCase() === filter);

  const agents = ['ALL', ...Object.keys(AGENT_META).filter(a => byAgent[a] > 0)];

  return (
    <div style={{
      background: colors.bg.secondary,
      border: `1px solid ${colors.border.default}`,
      borderRadius: 12,
      padding: '20px 24px',
      marginBottom: 24,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 20 }}>📎</span>
          <div>
            <div style={{ color: GOLD, fontSize: 14, fontWeight: 700, letterSpacing: '0.05em' }}>
              CLAUDE CAPTURES
            </div>
            <div style={{ color: colors.text.secondary, fontSize: 12, marginTop: 2 }}>
              Intelligence drops from V AgentForce · auto-routed to Obsidian
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            background: 'rgba(201,168,76,0.15)',
            color: GOLD,
            border: `1px solid rgba(201,168,76,0.25)`,
            borderRadius: 6,
            padding: '4px 10px',
            fontSize: 12,
            fontWeight: 600,
          }}>
            {total} total
          </span>
          <button
            onClick={load}
            style={{
              background: 'rgba(45,212,191,0.1)',
              border: `1px solid rgba(45,212,191,0.2)`,
              borderRadius: 6,
              color: TEAL,
              padding: '4px 10px',
              fontSize: 11,
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            ↻ refresh
          </button>
        </div>
      </div>

      {/* Agent filter pills */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 16 }}>
        {agents.map(a => {
          const meta = a === 'ALL' ? { emoji: '📋', color: '#888', bg: 'rgba(136,136,136,0.12)' } : agentMeta(a);
          const active = filter === a;
          return (
            <button
              key={a}
              onClick={() => setFilter(a)}
              style={{
                background: active ? meta.bg : 'rgba(255,255,255,0.03)',
                border: `1px solid ${active ? meta.color : colors.border.subtle}`,
                borderRadius: 6,
                color: active ? meta.color : colors.text.muted,
                padding: '4px 10px',
                fontSize: 11,
                fontWeight: active ? 700 : 400,
                cursor: 'pointer',
                fontFamily: 'inherit',
                transition: 'all 0.15s',
              }}
            >
              {meta.emoji} {a} {a !== 'ALL' && byAgent[a] ? `(${byAgent[a]})` : ''}
            </button>
          );
        })}
      </div>

      {/* How-to-save hint when empty */}
      {total === 0 && !loading && (
        <div style={{
          background: 'rgba(201,168,76,0.06)',
          border: `1px solid rgba(201,168,76,0.15)`,
          borderRadius: 8,
          padding: '16px',
          marginBottom: 16,
        }}>
          <div style={{ color: GOLD, fontWeight: 700, fontSize: 12, marginBottom: 6 }}>
            ⚡ How to capture Claude output here
          </div>
          <div style={{ color: colors.text.secondary, fontSize: 11, lineHeight: 1.6 }}>
            1. Get a response from V AgentForce on your phone<br />
            2. Copy the response<br />
            3. Send to Telegram bot: <code style={{ color: TEAL }}>/save [paste content]</code><br />
            4. Agent auto-detected → written to Obsidian → appears here
          </div>
        </div>
      )}

      {/* Captures list */}
      {loading ? (
        <div style={{ color: colors.text.secondary, fontSize: 12, textAlign: 'center', padding: '20px 0' }}>
          Loading captures…
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ color: colors.text.muted, fontSize: 12, textAlign: 'center', padding: '12px 0' }}>
          No captures for {filter} yet.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(cap => {
            const meta = agentMeta(cap.agent);
            const isOpen = expanded === cap.id;
            return (
              <div
                key={cap.id}
                style={{
                  background: isOpen ? meta.bg : 'rgba(255,255,255,0.02)',
                  border: `1px solid ${isOpen ? meta.color : colors.border.subtle}`,
                  borderRadius: 8,
                  overflow: 'hidden',
                  transition: 'all 0.15s',
                }}
              >
                {/* Row header */}
                <div
                  onClick={() => setExpanded(isOpen ? null : cap.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '10px 14px',
                    cursor: 'pointer',
                  }}
                >
                  {/* Agent badge */}
                  <span style={{
                    background: meta.bg,
                    color: meta.color,
                    border: `1px solid ${meta.color}40`,
                    borderRadius: 4,
                    padding: '2px 8px',
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: '0.06em',
                    whiteSpace: 'nowrap',
                    minWidth: 80,
                    textAlign: 'center',
                  }}>
                    {meta.emoji} {cap.agent}
                  </span>

                  {/* Title */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      color: colors.text.primary,
                      fontSize: 12,
                      fontWeight: 600,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}>
                      {cap.title}
                    </div>
                    <div style={{ color: colors.text.muted, fontSize: 10, marginTop: 2 }}>
                      {cap.vault_path.split('/').slice(0, 2).join('/')}
                    </div>
                  </div>

                  {/* Status + time */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                    <span style={{
                      fontSize: 10,
                      color: cap.obsidian_written ? '#4ade80' : '#fb923c',
                      background: cap.obsidian_written ? 'rgba(74,222,128,0.1)' : 'rgba(251,146,60,0.1)',
                      border: `1px solid ${cap.obsidian_written ? 'rgba(74,222,128,0.2)' : 'rgba(251,146,60,0.2)'}`,
                      borderRadius: 4,
                      padding: '1px 6px',
                    }}>
                      {cap.obsidian_written ? '🟢 Obsidian' : '🟡 SQLite'}
                    </span>
                    <span style={{ color: colors.text.muted, fontSize: 10 }}>
                      {timeAgo(cap.created_at)}
                    </span>
                    <span style={{ color: colors.text.muted, fontSize: 12 }}>
                      {isOpen ? '▲' : '▼'}
                    </span>
                  </div>
                </div>

                {/* Expanded body */}
                {isOpen && (
                  <div style={{
                    borderTop: `1px solid ${colors.border.subtle}`,
                    padding: '12px 14px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 10,
                  }}>
                    {/* Content preview */}
                    <div style={{
                      background: 'rgba(0,0,0,0.2)',
                      borderRadius: 6,
                      padding: '10px 12px',
                      fontSize: 11,
                      color: colors.text.secondary,
                      lineHeight: 1.6,
                      whiteSpace: 'pre-wrap',
                      maxHeight: 200,
                      overflowY: 'auto',
                    }}>
                      {cap.content.slice(0, 600)}{cap.content.length > 600 ? '…' : ''}
                    </div>

                    {/* Revenue angle */}
                    <div style={{
                      background: 'rgba(201,168,76,0.08)',
                      border: '1px solid rgba(201,168,76,0.15)',
                      borderRadius: 6,
                      padding: '8px 12px',
                      fontSize: 11,
                      color: GOLD,
                    }}>
                      {cap.revenue_angle}
                    </div>

                    {/* Vault path */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 10, color: colors.text.muted }}>📁 Vault:</span>
                      <code style={{ fontSize: 10, color: TEAL }}>
                        V AgentForce/{cap.vault_path}
                      </code>
                    </div>

                    {/* Source URL */}
                    {cap.source_url && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 10, color: colors.text.muted }}>🔗 Source:</span>
                        <a
                          href={cap.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ fontSize: 10, color: colors.accent.education }}
                        >
                          {cap.source_url.slice(0, 60)}…
                        </a>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Footer */}
      {total > 0 && (
        <div style={{
          marginTop: 14,
          padding: '10px 12px',
          background: 'rgba(45,212,191,0.05)',
          border: '1px solid rgba(45,212,191,0.12)',
          borderRadius: 6,
          fontSize: 10,
          color: colors.text.muted,
        }}>
          💡 Save Claude outputs: send <code style={{ color: TEAL }}>/save [content]</code> to your Telegram bot
          — agent auto-detected → Obsidian → here
        </div>
      )}
    </div>
  );
}

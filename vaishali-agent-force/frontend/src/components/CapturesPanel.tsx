import React, { useEffect, useState, useCallback } from 'react';
import { colors } from '../theme/colors';

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
  enriched?: number;
  signal_rating?: string;
  summary?: string;
  insights_json?: string;
}

interface CaptureStats {
  total: number;
  enriched: number;
  must_act: number;
  obsidian_written: number;
  by_agent: Record<string, number>;
}

const AGENT_META: Record<string, { emoji: string; color: string; bg: string }> = {
  SENTINEL:  { emoji: '🎖️', color: '#c9a84c', bg: 'rgba(201,168,76,0.12)' },
  FORGE:     { emoji: '🏗️', color: '#2dd4bf', bg: 'rgba(45,212,191,0.12)' },
  AMPLIFY:   { emoji: '📱', color: '#a78bfa', bg: 'rgba(167,139,250,0.12)' },
  PHOENIX:   { emoji: '💰', color: '#fb923c', bg: 'rgba(251,146,60,0.12)' },
  VITALITY:  { emoji: '⚡', color: '#4ade80', bg: 'rgba(74,222,128,0.12)' },
  CIPHER:    { emoji: '🔍', color: '#60a5fa', bg: 'rgba(96,165,250,0.12)' },
  AEGIS:     { emoji: '🛡️', color: '#f87171', bg: 'rgba(248,113,113,0.12)' },
  NEXUS:     { emoji: '🔮', color: '#e879f9', bg: 'rgba(232,121,249,0.12)' },
  ATLAS:     { emoji: '🗺️', color: '#fbbf24', bg: 'rgba(251,191,36,0.12)' },
  COLOSSUS:  { emoji: '⚔️', color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
};

const DEFAULT_META = { emoji: '📎', color: '#888', bg: 'rgba(136,136,136,0.12)' };
function meta(agent: string) { return AGENT_META[agent.toUpperCase()] ?? DEFAULT_META; }

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)  return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)  return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const SIGNAL_LABEL: Record<string, { label: string; color: string; bg: string }> = {
  '🟢': { label: '🟢 Must-Act', color: '#4ade80', bg: 'rgba(74,222,128,0.12)' },
  '🟡': { label: '🟡 Valuable', color: '#fbbf24', bg: 'rgba(251,191,36,0.12)' },
  '🔴': { label: '🔴 Noise',    color: '#6b7280', bg: 'rgba(107,114,128,0.08)' },
};

export function CapturesPanel() {
  const [captures, setCaptures] = useState<Capture[]>([]);
  const [stats, setStats] = useState<CaptureStats | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [filter, setFilter] = useState<string>('ALL');
  const [signalFilter, setSignalFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [capturesRes, statsRes] = await Promise.all([
        fetch('/api/captures?limit=50'),
        fetch('/api/captures/stats'),
      ]);
      if (capturesRes.ok) {
        const data = await capturesRes.json();
        setCaptures(data.captures ?? []);
      }
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
    } catch (_) {}
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    load();
    const iv = setInterval(load, 30_000);
    const onFocus = () => load();
    window.addEventListener('focus', onFocus);
    return () => { clearInterval(iv); window.removeEventListener('focus', onFocus); };
  }, [load]);

  const filtered = captures.filter(c => {
    if (filter !== 'ALL' && c.agent.toUpperCase() !== filter) return false;
    if (signalFilter !== 'ALL' && c.signal_rating !== signalFilter) return false;
    return true;
  });

  const agents = ['ALL', ...Object.keys(AGENT_META).filter(a => stats?.by_agent?.[a])];

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
          <span style={{ fontSize: 20 }}>🧠</span>
          <div>
            <div style={{ color: GOLD, fontSize: 14, fontWeight: 700, letterSpacing: '0.05em' }}>
              INTELLIGENCE FEED
            </div>
            <div style={{ color: colors.text.secondary, fontSize: 12, marginTop: 2 }}>
              Enriched by orchestrator · routed to Obsidian · golden thread active
            </div>
          </div>
        </div>
        <button onClick={load} style={{
          background: 'rgba(45,212,191,0.1)', border: `1px solid rgba(45,212,191,0.2)`,
          borderRadius: 6, color: TEAL, padding: '4px 10px', fontSize: 11,
          cursor: 'pointer', fontFamily: 'inherit',
        }}>↻ refresh</button>
      </div>

      {/* Stats strip */}
      {stats && (
        <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
          {[
            { label: 'Total', value: stats.total, color: GOLD },
            { label: 'Enriched', value: stats.enriched, color: TEAL },
            { label: 'Must-Act', value: stats.must_act, color: '#4ade80' },
            { label: 'In Obsidian', value: stats.obsidian_written, color: '#a78bfa' },
          ].map(s => (
            <div key={s.label} style={{
              background: `${s.color}12`, border: `1px solid ${s.color}30`,
              borderRadius: 8, padding: '8px 14px', display: 'flex', flexDirection: 'column', alignItems: 'center',
              minWidth: 80,
            }}>
              <span style={{ color: s.color, fontSize: 20, fontWeight: 800, lineHeight: 1 }}>{s.value}</span>
              <span style={{ color: colors.text.muted, fontSize: 10, marginTop: 4, fontWeight: 600,
                letterSpacing: '0.05em', textTransform: 'uppercase' as const }}>{s.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Signal filter */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
        {['ALL', '🟢', '🟡', '🔴'].map(s => {
          const active = signalFilter === s;
          const info = s === 'ALL' ? { label: 'All Signals', color: '#888', bg: 'rgba(136,136,136,0.08)' } : SIGNAL_LABEL[s];
          return (
            <button key={s} onClick={() => setSignalFilter(s)} style={{
              background: active ? info.bg : 'transparent',
              border: `1px solid ${active ? info.color + '50' : colors.border.subtle}`,
              borderRadius: 6, color: active ? info.color : colors.text.muted,
              padding: '3px 10px', fontSize: 11, fontWeight: active ? 700 : 400,
              cursor: 'pointer', fontFamily: 'inherit',
            }}>{info.label}</button>
          );
        })}
      </div>

      {/* Agent filter pills */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 16 }}>
        {agents.map(a => {
          const m = a === 'ALL' ? { emoji: '📋', color: '#888', bg: 'rgba(136,136,136,0.12)' } : meta(a);
          const active = filter === a;
          const count = a === 'ALL' ? stats?.total : stats?.by_agent?.[a];
          return (
            <button key={a} onClick={() => setFilter(a)} style={{
              background: active ? m.bg : 'rgba(255,255,255,0.03)',
              border: `1px solid ${active ? m.color : colors.border.subtle}`,
              borderRadius: 6, color: active ? m.color : colors.text.muted,
              padding: '4px 10px', fontSize: 11, fontWeight: active ? 700 : 400,
              cursor: 'pointer', fontFamily: 'inherit', transition: 'all 0.15s',
            }}>{m.emoji} {a} {count ? `(${count})` : ''}</button>
          );
        })}
      </div>

      {/* Empty state */}
      {stats?.total === 0 && !loading && (
        <div style={{
          background: 'rgba(201,168,76,0.06)', border: `1px solid rgba(201,168,76,0.15)`,
          borderRadius: 8, padding: 16, marginBottom: 16,
        }}>
          <div style={{ color: GOLD, fontWeight: 700, fontSize: 12, marginBottom: 6 }}>
            ⚡ Start the golden thread
          </div>
          <div style={{ color: colors.text.secondary, fontSize: 11, lineHeight: 1.6 }}>
            1. Type a thought in Claude Mobile<br />
            2. Send to Telegram: <code style={{ color: TEAL }}>/save [content]</code><br />
            3. Orchestrator enriches → Obsidian → appears here with insights + revenue angle<br />
            Or use iOS Shortcut "Drop to VAF" for one-tap capture from any app
          </div>
        </div>
      )}

      {/* Captures list */}
      {loading ? (
        <div style={{ color: colors.text.secondary, fontSize: 12, textAlign: 'center', padding: '20px 0' }}>
          Loading intelligence feed…
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ color: colors.text.muted, fontSize: 12, textAlign: 'center', padding: '12px 0' }}>
          No captures match this filter.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(cap => {
            const m = meta(cap.agent);
            const isOpen = expanded === cap.id;
            const signal = SIGNAL_LABEL[cap.signal_rating || '🟡'] || SIGNAL_LABEL['🟡'];
            const isEnriched = !!cap.enriched;
            let insights: string[] = [];
            try { insights = JSON.parse(cap.insights_json || '[]'); } catch {}

            return (
              <div key={cap.id} style={{
                background: isOpen ? m.bg : 'rgba(255,255,255,0.02)',
                border: `1px solid ${isOpen ? m.color : colors.border.subtle}`,
                borderRadius: 8, overflow: 'hidden', transition: 'all 0.15s',
                borderLeft: cap.signal_rating === '🟢' ? `3px solid #4ade80` : undefined,
              }}>
                {/* Row header */}
                <div onClick={() => setExpanded(isOpen ? null : cap.id)} style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', cursor: 'pointer',
                }}>
                  {/* Agent badge */}
                  <span style={{
                    background: m.bg, color: m.color, border: `1px solid ${m.color}40`,
                    borderRadius: 4, padding: '2px 8px', fontSize: 10, fontWeight: 700,
                    letterSpacing: '0.06em', whiteSpace: 'nowrap', minWidth: 80, textAlign: 'center',
                  }}>{m.emoji} {cap.agent}</span>

                  {/* Title + summary */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      color: colors.text.primary, fontSize: 12, fontWeight: 600,
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>{cap.title}</div>
                    {isEnriched && cap.summary && (
                      <div style={{ color: colors.text.muted, fontSize: 10, marginTop: 2,
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}>{cap.summary}</div>
                    )}
                  </div>

                  {/* Status badges */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                    {/* Signal rating */}
                    <span style={{
                      fontSize: 10, color: signal.color, background: signal.bg,
                      border: `1px solid ${signal.color}30`, borderRadius: 4, padding: '1px 6px',
                    }}>{cap.signal_rating || '🟡'}</span>

                    {/* Enriched badge */}
                    {isEnriched && (
                      <span style={{
                        fontSize: 9, color: TEAL, background: 'rgba(45,212,191,0.1)',
                        border: '1px solid rgba(45,212,191,0.2)', borderRadius: 4, padding: '1px 5px',
                      }}>🧠</span>
                    )}

                    {/* Obsidian status */}
                    <span style={{
                      fontSize: 10,
                      color: cap.obsidian_written ? '#4ade80' : '#fb923c',
                      background: cap.obsidian_written ? 'rgba(74,222,128,0.1)' : 'rgba(251,146,60,0.1)',
                      border: `1px solid ${cap.obsidian_written ? 'rgba(74,222,128,0.2)' : 'rgba(251,146,60,0.2)'}`,
                      borderRadius: 4, padding: '1px 6px',
                    }}>{cap.obsidian_written ? '🟢' : '🟡'}</span>

                    <span style={{ color: colors.text.muted, fontSize: 10 }}>{timeAgo(cap.created_at)}</span>
                    <span style={{ color: colors.text.muted, fontSize: 12 }}>{isOpen ? '▲' : '▼'}</span>
                  </div>
                </div>

                {/* Expanded body */}
                {isOpen && (
                  <div style={{
                    borderTop: `1px solid ${colors.border.subtle}`,
                    padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 10,
                  }}>
                    {/* Insights */}
                    {insights.length > 0 && (
                      <div style={{
                        background: 'rgba(45,212,191,0.06)', border: '1px solid rgba(45,212,191,0.12)',
                        borderRadius: 6, padding: '10px 12px',
                      }}>
                        <div style={{ fontSize: 10, fontWeight: 700, color: TEAL, letterSpacing: '0.08em',
                          textTransform: 'uppercase' as const, marginBottom: 6 }}>Key Insights</div>
                        {insights.map((ins, i) => (
                          <div key={i} style={{ fontSize: 11, color: colors.text.secondary, lineHeight: 1.5,
                            paddingLeft: 12, position: 'relative', marginBottom: 4,
                          }}>
                            <span style={{ position: 'absolute', left: 0, color: TEAL }}>→</span>
                            {ins}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Content */}
                    <div style={{
                      background: 'rgba(0,0,0,0.2)', borderRadius: 6, padding: '10px 12px',
                      fontSize: 11, color: colors.text.secondary, lineHeight: 1.6,
                      whiteSpace: 'pre-wrap', maxHeight: 200, overflowY: 'auto',
                    }}>{cap.content.slice(0, 600)}{cap.content.length > 600 ? '…' : ''}</div>

                    {/* Revenue angle */}
                    <div style={{
                      background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.15)',
                      borderRadius: 6, padding: '8px 12px', fontSize: 11, color: GOLD,
                    }}>{cap.revenue_angle}</div>

                    {/* Vault + source */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 10, color: colors.text.muted }}>📁</span>
                        <code style={{ fontSize: 10, color: TEAL }}>V AgentForce/{cap.vault_path}</code>
                      </div>
                      {cap.source_url && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 10, color: colors.text.muted }}>🔗</span>
                          <a href={cap.source_url} target="_blank" rel="noopener noreferrer"
                            style={{ fontSize: 10, color: colors.accent.education }}
                          >{cap.source_url.slice(0, 60)}{cap.source_url.length > 60 ? '…' : ''}</a>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Footer */}
      <div style={{
        marginTop: 14, padding: '10px 12px',
        background: 'rgba(45,212,191,0.05)', border: '1px solid rgba(45,212,191,0.12)',
        borderRadius: 6, fontSize: 10, color: colors.text.muted,
      }}>
        💡 Telegram: <code style={{ color: TEAL }}>/save</code> (enriched) · <code style={{ color: TEAL }}>/quick</code> (fast) · iOS Shortcut: "Drop to VAF"
      </div>
    </div>
  );
}

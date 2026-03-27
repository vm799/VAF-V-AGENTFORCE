import React, { useEffect, useState, useCallback, useRef } from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';

interface Insight {
  id: string;
  title: string;
  url: string;
  summary: string;
  category: string;
  key_insights: string[];
  key_topics: string[];
  action_items: string[];
  quality_score: number;
  notebooklm_summary?: string;
  created_at: string;
}

const CATEGORY_META: Record<string, { emoji: string; label: string; color: string }> = {
  recipe:    { emoji: '🍳', label: 'Recipe',     color: '#f59e0b' },
  finance:   { emoji: '💰', label: 'Finance',    color: '#10b981' },
  ai:        { emoji: '🤖', label: 'AI & ML',    color: '#8b5cf6' },
  tech:      { emoji: '💻', label: 'Technology', color: '#3b82f6' },
  health:    { emoji: '🏃', label: 'Health',     color: '#ec4899' },
  career:    { emoji: '🎯', label: 'Career',     color: '#f97316' },
  personal:  { emoji: '📝', label: 'Personal',   color: '#6b7280' },
  education: { emoji: '📚', label: 'Education',  color: '#06b6d4' },
  research:  { emoji: '🔬', label: 'Research',   color: '#a78bfa' },
};

function StatusDot({ lastUpdated, onRefresh }: { lastUpdated: Date | null; onRefresh?: () => void }) {
  const age = lastUpdated ? Math.floor((Date.now() - lastUpdated.getTime()) / 1000) : null;
  const label = age === null ? 'Never' : age < 5 ? 'Just now' : age < 60 ? `${age}s ago` : `${Math.floor(age / 60)}m ago`;
  return (
    <button
      onClick={onRefresh}
      title="Click to refresh"
      style={{
        display: 'flex', alignItems: 'center', gap: 5, background: 'none', border: 'none',
        cursor: onRefresh ? 'pointer' : 'default', padding: 0,
      }}>
      <span style={{
        width: 7, height: 7, borderRadius: '50%',
        backgroundColor: age !== null && age < 30 ? '#10b981' : '#6b7280',
        display: 'inline-block', flexShrink: 0,
      }} />
      <span style={{ fontSize: '10px', color: '#6b7280', fontFamily: 'monospace' }}>{label}</span>
    </button>
  );
}

const QUALITY_DOTS = (score: number) => {
  const filled = Math.round(score / 2);
  return Array.from({ length: 5 }, (_, i) => (
    <span key={i} style={{ color: i < filled ? '#f59e0b' : '#374151', fontSize: '10px' }}>●</span>
  ));
};

export function InsightsPanel() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [apiDown, setApiDown] = useState(false);
  const [newCount, setNewCount] = useState(0);
  const prevCountRef = useRef(0);

  const fetchInsights = useCallback((silent = false) => {
    if (!silent) setLoading(true);
    fetch('/api/insights?limit=50')
      .then(r => {
        if (!r.ok) throw new Error('api_down');
        return r.json();
      })
      .then(d => {
        const items: Insight[] = d.insights || [];
        setInsights(items);
        setApiDown(false);
        setLastUpdated(new Date());
        const diff = items.length - prevCountRef.current;
        if (diff > 0 && prevCountRef.current > 0) setNewCount(diff);
        prevCountRef.current = items.length;
      })
      .catch(() => setApiDown(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchInsights();
    // Live poll every 15 seconds — catches insights as they arrive from the bot
    const interval = setInterval(() => fetchInsights(true), 15_000);
    // Also refresh when tab regains focus
    const onFocus = () => fetchInsights(true);
    window.addEventListener('focus', onFocus);
    return () => { clearInterval(interval); window.removeEventListener('focus', onFocus); };
  }, [fetchInsights]);

  const categories = Array.from(new Set(insights.map(i => i.category))).filter(Boolean);
  const filtered = activeCategory ? insights.filter(i => i.category === activeCategory) : insights;

  if (loading) return (
    <div style={cardStyle}>
      <h3 style={headingStyle}>🧠 Insights</h3>
      <p style={{ color: colors.text.muted, margin: 0 }}>Loading...</p>
    </div>
  );

  if (apiDown) return (
    <div style={cardStyle}>
      <h3 style={headingStyle}>🧠 Insights</h3>
      <div style={{
        background: '#ef444415', border: '1px solid #ef444430', borderRadius: 8,
        padding: '12px 16px', marginBottom: 12,
      }}>
        <p style={{ color: '#ef4444', margin: '0 0 6px', fontWeight: 600, fontSize: '13px' }}>
          ⚠️ Dashboard API not running
        </p>
        <p style={{ color: colors.text.secondary, margin: '0 0 8px', fontSize: typography.sizes.small }}>
          Open a terminal in your project folder and run:
        </p>
        <code style={{
          display: 'block', background: '#0f0f0f', color: '#10b981',
          padding: '8px 12px', borderRadius: 6, fontSize: '13px', fontFamily: 'monospace',
        }}>./vaf.sh quick</code>
        <p style={{ color: colors.text.muted, margin: '8px 0 0', fontSize: '11px' }}>
          This starts the API + Telegram bot. Dashboard auto-connects when it's up.
        </p>
      </div>
    </div>
  );

  if (!insights.length) return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <h3 style={{ ...headingStyle, margin: 0 }}>🧠 Insights</h3>
        <StatusDot lastUpdated={lastUpdated} />
      </div>
      <p style={{ color: colors.text.secondary, margin: '0 0 12px' }}>
        No insights yet. Drop any link into Telegram — finance articles, tech posts, research papers, anything.
      </p>
      <p style={{ color: colors.text.muted, margin: 0, fontSize: typography.sizes.small }}>
        The bot classifies it, saves to your Obsidian vault, then sends it to NotebookLM for AI analysis. Results appear here within ~60 seconds.
      </p>
    </div>
  );

  return (
    <div style={cardStyle}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <h3 style={{ ...headingStyle, margin: 0 }}>
          🧠 Insights
          <span style={{ color: colors.text.muted, fontWeight: 400, fontSize: typography.sizes.small, marginLeft: 8 }}>
            {filtered.length}{activeCategory ? ` ${CATEGORY_META[activeCategory]?.label || activeCategory}` : ' total'}
          </span>
          {newCount > 0 && (
            <span
              onClick={() => setNewCount(0)}
              style={{
                marginLeft: 8, background: '#10b981', color: '#fff',
                fontSize: '10px', fontWeight: 700, padding: '2px 7px',
                borderRadius: 10, cursor: 'pointer', verticalAlign: 'middle',
              }}>
              +{newCount} new
            </span>
          )}
        </h3>
        <StatusDot lastUpdated={lastUpdated} onRefresh={() => fetchInsights(true)} />
      </div>

      {/* Category filter pills */}
      {categories.length > 1 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
          <button
            onClick={() => setActiveCategory(null)}
            style={pillStyle(activeCategory === null)}
          >All</button>
          {categories.map(cat => {
            const m = CATEGORY_META[cat] || { emoji: '🔬', label: cat, color: '#a78bfa' };
            return (
              <button
                key={cat}
                onClick={() => setActiveCategory(activeCategory === cat ? null : cat)}
                style={pillStyle(activeCategory === cat, m.color)}
              >
                {m.emoji} {m.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Insight cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {filtered.map(ins => {
          const meta = CATEGORY_META[ins.category] || { emoji: '🔬', label: ins.category, color: '#a78bfa' };
          const isOpen = expanded === ins.id;

          return (
            <div
              key={ins.id}
              style={{
                backgroundColor: colors.bg.primary,
                borderRadius: 8,
                border: `1px solid ${isOpen ? meta.color + '60' : colors.border.subtle}`,
                overflow: 'hidden',
                cursor: 'pointer',
                transition: 'border-color 0.15s',
              }}
              onClick={() => setExpanded(isOpen ? null : ins.id)}
            >
              {/* Card header */}
              <div style={{ padding: '10px 14px' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                  {/* Category badge */}
                  <span style={{
                    flexShrink: 0,
                    backgroundColor: meta.color + '20',
                    color: meta.color,
                    fontSize: '10px',
                    fontWeight: 600,
                    padding: '2px 7px',
                    borderRadius: 10,
                    border: `1px solid ${meta.color}40`,
                    marginTop: 2,
                  }}>
                    {meta.emoji} {meta.label}
                  </span>

                  {/* NLM badge if enriched */}
                  {ins.notebooklm_summary && (
                    <span style={{
                      flexShrink: 0,
                      backgroundColor: '#8b5cf620',
                      color: '#8b5cf6',
                      fontSize: '10px',
                      fontWeight: 600,
                      padding: '2px 6px',
                      borderRadius: 10,
                      border: '1px solid #8b5cf640',
                      marginTop: 2,
                    }}>🔬 NLM</span>
                  )}

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <a
                      href={ins.url}
                      target="_blank"
                      rel="noreferrer"
                      onClick={e => e.stopPropagation()}
                      style={{
                        color: colors.text.primary,
                        textDecoration: 'none',
                        fontWeight: typography.weights.medium,
                        fontSize: typography.sizes.body,
                        display: 'block',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >{ins.title}</a>
                  </div>

                  <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
                    <div style={{ display: 'flex', gap: 1 }}>{QUALITY_DOTS(ins.quality_score)}</div>
                    <span style={{ fontSize: '10px', color: colors.text.muted }}>{ins.created_at?.slice(0, 10)}</span>
                  </div>
                </div>

                {/* Summary */}
                {ins.summary && (
                  <p style={{
                    margin: '6px 0 0',
                    color: colors.text.secondary,
                    fontSize: typography.sizes.small,
                    lineHeight: 1.5,
                  }}>
                    {ins.summary.slice(0, isOpen ? 999 : 160)}{!isOpen && ins.summary.length > 160 ? '…' : ''}
                  </p>
                )}

                {/* Topic pills */}
                {ins.key_topics?.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
                    {ins.key_topics.slice(0, 6).map(t => (
                      <span key={t} style={{
                        backgroundColor: colors.bg.secondary,
                        color: colors.text.muted,
                        fontSize: '10px',
                        padding: '1px 6px',
                        borderRadius: 8,
                        border: `1px solid ${colors.border.subtle}`,
                      }}>{t}</span>
                    ))}
                  </div>
                )}
              </div>

              {/* Expanded detail */}
              {isOpen && (
                <div style={{ borderTop: `1px solid ${colors.border.subtle}`, padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {ins.key_insights?.length > 0 && (
                    <div>
                      <p style={labelStyle}>Key insights</p>
                      {ins.key_insights.map((ki, i) => (
                        <p key={i} style={{ margin: '4px 0', color: colors.text.primary, fontSize: typography.sizes.small, lineHeight: 1.55 }}>
                          • {ki}
                        </p>
                      ))}
                    </div>
                  )}

                  {ins.notebooklm_summary && (
                    <div>
                      <p style={{ ...labelStyle, color: '#8b5cf6' }}>🔬 NotebookLM</p>
                      <p style={{ margin: 0, color: colors.text.secondary, fontSize: typography.sizes.small, lineHeight: 1.55 }}>
                        {ins.notebooklm_summary}
                      </p>
                    </div>
                  )}

                  {ins.action_items?.length > 0 && (
                    <div>
                      <p style={labelStyle}>Action items</p>
                      {ins.action_items.map((ai, i) => (
                        <p key={i} style={{ margin: '3px 0', color: '#10b981', fontSize: typography.sizes.small }}>
                          ✅ {ai}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  backgroundColor: colors.bg.secondary,
  borderRadius: 12,
  padding: 24,
  border: `1px solid ${colors.border.subtle}`,
};

const headingStyle: React.CSSProperties = {
  fontSize: typography.sizes.h3,
  fontWeight: typography.weights.semibold,
  color: colors.text.primary,
  margin: '0 0 16px',
};

const labelStyle: React.CSSProperties = {
  fontSize: '10px',
  fontWeight: typography.weights.semibold,
  color: colors.text.muted,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  margin: '0 0 4px',
};

const pillStyle = (active: boolean, color?: string): React.CSSProperties => ({
  background: active ? (color ? color + '25' : '#ffffff15') : 'transparent',
  color: active ? (color || colors.text.primary) : colors.text.muted,
  border: `1px solid ${active ? (color ? color + '50' : colors.border.subtle) : colors.border.subtle}`,
  borderRadius: 20,
  padding: '3px 10px',
  fontSize: '11px',
  cursor: 'pointer',
  fontFamily: typography.fontFamily,
  transition: 'all 0.15s',
});

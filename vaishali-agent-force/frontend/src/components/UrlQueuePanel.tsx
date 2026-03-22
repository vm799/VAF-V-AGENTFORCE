import React, { useEffect, useState, useCallback } from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';

interface QueueItem {
  id: string;
  url: string;
  title: string;
  category: string;
  status: 'pending' | 'done' | 'failed' | 'processing';
  queued_at: string;
  processed_at?: string;
  nlm_summary?: string;
  error?: string;
}

interface UrlsResponse {
  urls: QueueItem[];
  total: number;
  pending: number;
  done: number;
  failed: number;
}

const CATEGORY_META: Record<string, { emoji: string; color: string }> = {
  recipe:    { emoji: '🍳', color: '#f59e0b' },
  finance:   { emoji: '💰', color: '#10b981' },
  ai:        { emoji: '🤖', color: '#8b5cf6' },
  tech:      { emoji: '💻', color: '#3b82f6' },
  health:    { emoji: '🏃', color: '#ec4899' },
  career:    { emoji: '🎯', color: '#f97316' },
  personal:  { emoji: '📝', color: '#6b7280' },
  education: { emoji: '📚', color: '#06b6d4' },
  research:  { emoji: '🔬', color: '#a78bfa' },
};

const STATUS_META: Record<string, { label: string; color: string; bg: string; dot: string }> = {
  pending:    { label: 'Queued for NLM', color: '#fbbf24', bg: '#fbbf2415', dot: '⏳' },
  processing: { label: 'Processing…',   color: '#60a5fa', bg: '#60a5fa15', dot: '⚙️' },
  done:       { label: 'NLM done',       color: '#10b981', bg: '#10b98115', dot: '✅' },
  failed:     { label: 'Failed',         color: '#f87171', bg: '#f8717115', dot: '❌' },
};

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function UrlQueuePanel() {
  const [data, setData] = useState<UrlsResponse | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [activeStatus, setActiveStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchUrls = useCallback((silent = false) => {
    if (!silent) setLoading(true);
    fetch('/api/urls')
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d => { setData(d); setError(false); })
      .catch(() => setError(true))
      .finally(() => { if (!silent) setLoading(false); });
  }, []);

  useEffect(() => {
    fetchUrls();
    const interval = setInterval(() => fetchUrls(true), 20_000);
    const onFocus = () => fetchUrls(true);
    window.addEventListener('focus', onFocus);
    return () => { clearInterval(interval); window.removeEventListener('focus', onFocus); };
  }, [fetchUrls]);

  if (loading) return (
    <div style={cardStyle}>
      <h3 style={headingStyle}>🔗 Saved Links</h3>
      <p style={{ color: colors.text.muted, margin: 0, fontSize: typography.sizes.small }}>Loading…</p>
    </div>
  );

  if (error || !data) return (
    <div style={cardStyle}>
      <h3 style={headingStyle}>🔗 Saved Links</h3>
      <p style={{ color: colors.text.muted, margin: 0, fontSize: typography.sizes.small }}>
        No links yet — drop a URL in Telegram to get started.
      </p>
    </div>
  );

  const { urls, total, pending, done, failed } = data;

  const filtered = activeStatus ? urls.filter(u => u.status === activeStatus) : urls;

  return (
    <div style={cardStyle}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <div>
          <h3 style={{ ...headingStyle, margin: '0 0 6px' }}>
            🔗 Saved Links
            <span style={{ color: colors.text.muted, fontWeight: 400, fontSize: typography.sizes.small, marginLeft: 8 }}>
              {total} total
            </span>
          </h3>
          <p style={{ margin: 0, fontSize: '11px', color: colors.text.muted }}>
            NLM batch runs at 8pm daily · {pending} pending · {done} processed
          </p>
        </div>
        <button
          onClick={() => fetchUrls(true)}
          style={{
            background: 'none', border: `1px solid ${colors.border.subtle}`,
            borderRadius: 6, padding: '4px 10px', cursor: 'pointer',
            color: colors.text.muted, fontSize: '11px', fontFamily: typography.fontFamily,
          }}
        >↻ Refresh</button>
      </div>

      {/* Stats row */}
      {total > 0 && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
          {[
            { key: null,        label: 'All',     count: total,  color: colors.text.secondary },
            { key: 'pending',   label: '⏳ Queued', count: pending, color: '#fbbf24' },
            { key: 'done',      label: '✅ Done',   count: done,   color: '#10b981' },
            { key: 'failed',    label: '❌ Failed', count: failed, color: '#f87171' },
          ].filter(s => s.count > 0 || s.key === null).map(({ key, label, count, color }) => (
            <button
              key={String(key)}
              onClick={() => setActiveStatus(activeStatus === key ? null : key)}
              style={{
                background: activeStatus === key ? color + '15' : 'transparent',
                border: `1px solid ${activeStatus === key ? color + '50' : colors.border.subtle}`,
                borderRadius: 16, padding: '3px 10px', cursor: 'pointer',
                color: activeStatus === key ? color : colors.text.muted,
                fontSize: '11px', fontFamily: typography.fontFamily,
                display: 'flex', alignItems: 'center', gap: 5,
              }}
            >
              {label}
              <span style={{
                background: color + '25', color, borderRadius: 8,
                padding: '0 5px', fontWeight: 700, fontSize: '10px',
              }}>{count}</span>
            </button>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!total && (
        <div style={{
          textAlign: 'center', padding: '32px 16px',
          border: `1px dashed ${colors.border.default}`, borderRadius: 8,
        }}>
          <p style={{ margin: '0 0 6px', fontSize: '28px' }}>🔗</p>
          <p style={{ margin: '0 0 4px', color: colors.text.secondary, fontWeight: 600 }}>No links saved yet</p>
          <p style={{ margin: 0, color: colors.text.muted, fontSize: typography.sizes.small }}>
            Drop any URL in Telegram — articles, videos, research papers, anything. They'll appear here and get processed by NotebookLM tonight at 8pm.
          </p>
        </div>
      )}

      {/* URL list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {filtered.map(item => {
          const catMeta = CATEGORY_META[item.category] || { emoji: '🔗', color: '#6b7280' };
          const statusMeta = STATUS_META[item.status] || STATUS_META.pending;
          const isOpen = expanded === item.id;

          return (
            <div
              key={item.id}
              style={{
                backgroundColor: colors.bg.primary,
                border: `1px solid ${isOpen ? catMeta.color + '50' : colors.border.subtle}`,
                borderRadius: 8, overflow: 'hidden',
                cursor: 'pointer', transition: 'border-color 0.15s',
              }}
              onClick={() => setExpanded(isOpen ? null : item.id)}
            >
              {/* Row */}
              <div style={{ padding: '9px 12px', display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                {/* Category emoji */}
                <span style={{ fontSize: '16px', flexShrink: 0, marginTop: 1 }}>{catMeta.emoji}</span>

                {/* Main content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                    {/* Clickable title */}
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      onClick={e => e.stopPropagation()}
                      style={{
                        color: colors.text.primary, textDecoration: 'none',
                        fontWeight: typography.weights.medium,
                        fontSize: typography.sizes.small,
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                        display: 'block', flex: 1,
                        ':hover': { textDecoration: 'underline' },
                      } as React.CSSProperties}
                    >
                      {item.title || item.url}
                    </a>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    {/* Status badge */}
                    <span style={{
                      background: statusMeta.bg, color: statusMeta.color,
                      fontSize: '10px', fontWeight: 600, padding: '1px 6px',
                      borderRadius: 8, border: `1px solid ${statusMeta.color}30`,
                      flexShrink: 0,
                    }}>
                      {statusMeta.dot} {statusMeta.label}
                    </span>

                    {/* Category label */}
                    <span style={{
                      background: catMeta.color + '15', color: catMeta.color,
                      fontSize: '10px', padding: '1px 6px', borderRadius: 8,
                      border: `1px solid ${catMeta.color}30`, flexShrink: 0,
                    }}>
                      {item.category}
                    </span>

                    {/* Timestamp */}
                    <span style={{ fontSize: '10px', color: colors.text.muted }}>
                      {relativeTime(item.queued_at)}
                    </span>
                  </div>
                </div>

                {/* Expand chevron */}
                <span style={{
                  color: colors.text.muted, fontSize: '11px', flexShrink: 0,
                  transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s',
                }}>▼</span>
              </div>

              {/* Expanded detail */}
              {isOpen && (
                <div style={{
                  borderTop: `1px solid ${colors.border.subtle}`,
                  padding: '10px 12px',
                  display: 'flex', flexDirection: 'column', gap: 8,
                }}>
                  {/* URL */}
                  <div>
                    <p style={labelStyle}>URL</p>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        color: '#60a5fa', fontSize: '11px', fontFamily: 'monospace',
                        wordBreak: 'break-all', textDecoration: 'none',
                      }}
                    >
                      {item.url}
                    </a>
                  </div>

                  {/* NLM summary */}
                  {item.nlm_summary && (
                    <div>
                      <p style={{ ...labelStyle, color: '#8b5cf6' }}>🔬 NotebookLM Insight</p>
                      <p style={{
                        margin: 0, color: colors.text.secondary,
                        fontSize: typography.sizes.small, lineHeight: 1.55,
                        background: '#8b5cf608', padding: '8px 10px',
                        borderRadius: 6, borderLeft: '3px solid #8b5cf6',
                      }}>
                        {item.nlm_summary}
                      </p>
                    </div>
                  )}

                  {/* Pending notice */}
                  {item.status === 'pending' && (
                    <p style={{
                      margin: 0, color: '#fbbf24', fontSize: '11px',
                      background: '#fbbf2410', padding: '6px 10px', borderRadius: 6,
                    }}>
                      ⏳ Queued for tonight's 8pm NotebookLM batch run
                    </p>
                  )}

                  {/* Error */}
                  {item.status === 'failed' && item.error && (
                    <div>
                      <p style={{ ...labelStyle, color: '#f87171' }}>Error</p>
                      <p style={{
                        margin: 0, color: '#f87171', fontSize: '11px', fontFamily: 'monospace',
                        background: '#f8717110', padding: '6px 10px', borderRadius: 6,
                      }}>
                        {item.error}
                      </p>
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
  fontWeight: 700,
  color: colors.text.muted,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  margin: '0 0 4px',
};

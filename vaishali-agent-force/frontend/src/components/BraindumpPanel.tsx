import React from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';

interface BraindumpPanelProps {
  data: any;
}

const ACCENT = '#e879f9'; // Fuchsia/pink for braindump — distinct from other agents

const PRIORITY_EMOJI: Record<string, string> = {
  urgent: '\u{1F534}',   // red circle
  high: '\u{1F7E0}',     // orange circle
  medium: '\u{1F7E1}',   // yellow circle
  low: '\u{1F7E2}',      // green circle
  someday: '\u26AA',     // white circle
};

const CATEGORY_EMOJI: Record<string, string> = {
  work: '\u{1F4BC}',
  home: '\u{1F3E0}',
  personal: '\u{1F464}',
  health: '\u{1F3C3}',
  finance: '\u{1F4B0}',
  learning: '\u{1F4DA}',
  creative: '\u{1F3A8}',
};

const TYPE_EMOJI: Record<string, string> = {
  action: '\u26A1',
  todo: '\u2705',
  idea: '\u{1F4A1}',
  reflection: '\u{1FA9E}',
  question: '\u2753',
  reference: '\u{1F4CC}',
};

export function BraindumpPanel({ data }: BraindumpPanelProps) {
  const hasData = data && (data.total_thoughts > 0 || data.today_count > 0);

  return (
    <div style={panelStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <span style={{ fontSize: 28 }}>{'\u{1F9E0}'}</span>
        <h3 style={headerStyle}>Braindump</h3>
      </div>

      {!hasData ? (
        <p style={emptyStyle}>
          No thoughts captured yet — use /dump on Telegram to start brain dumping!
        </p>
      ) : (
        <>
          {/* Stats bar */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 16 }}>
            <StatBox label="Total" value={data.total_thoughts} />
            <StatBox label="Today" value={data.today_count} />
            <StatBox label="Actions" value={data.active_actions} highlight={data.active_actions > 0} />
          </div>

          {/* Category breakdown */}
          {data.by_category && Object.keys(data.by_category).length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <p style={labelStyle}>By Category</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {Object.entries(data.by_category).map(([cat, count]) => (
                  <span key={cat} style={chipStyle}>
                    {CATEGORY_EMOJI[cat] || '\u{1F4AD}'} {cat} ({count as number})
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Top actions */}
          {data.top_actions && data.top_actions.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <p style={labelStyle}>Top Actions</p>
              {data.top_actions.map((action: any) => (
                <div key={action.id} style={actionRowStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>{PRIORITY_EMOJI[action.priority] || '\u{1F7E1}'}</span>
                    <span>{CATEGORY_EMOJI[action.category] || '\u{1F4AD}'}</span>
                    <span style={{ fontSize: typography.sizes.small, color: colors.text.primary }}>
                      {action.title}
                    </span>
                  </div>
                  {action.when && (
                    <span style={{ fontSize: typography.sizes.xs, color: colors.text.muted }}>
                      {'\u{1F4C5}'} {action.when}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Recent thoughts */}
          {data.recent_thoughts && data.recent_thoughts.length > 0 && (
            <div>
              <p style={labelStyle}>Recent Thoughts</p>
              {data.recent_thoughts.slice(0, 6).map((thought: any) => (
                <div key={thought.id} style={thoughtRowStyle}>
                  <span>{TYPE_EMOJI[thought.type] || '\u{1F4AD}'}</span>
                  <span style={{ fontSize: typography.sizes.small, color: colors.text.secondary, flex: 1 }}>
                    {thought.title}
                  </span>
                  <span style={{
                    fontSize: typography.sizes.xs,
                    color: ACCENT,
                    backgroundColor: `${ACCENT}15`,
                    padding: '2px 6px',
                    borderRadius: 4,
                  }}>
                    {thought.type}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Mood line */}
          {data.mood && (
            <div style={{
              marginTop: 12,
              padding: '10px 12px',
              backgroundColor: colors.bg.primary,
              borderRadius: 6,
              borderLeft: `3px solid ${ACCENT}`,
            }}>
              <p style={{ margin: 0, fontSize: typography.sizes.small, color: colors.text.secondary }}>
                {'\u{1F4AD}'} {data.mood}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}


function StatBox({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  return (
    <div style={{
      padding: '8px 10px',
      backgroundColor: colors.bg.primary,
      borderRadius: 6,
      textAlign: 'center',
    }}>
      <p style={{ margin: 0, fontSize: typography.sizes.small, color: colors.text.muted }}>{label}</p>
      <p style={{
        margin: '2px 0',
        fontSize: typography.sizes.h3,
        fontWeight: typography.weights.semibold,
        color: highlight ? colors.status.warning : colors.text.primary,
      }}>
        {value}
      </p>
    </div>
  );
}


const panelStyle: React.CSSProperties = {
  backgroundColor: colors.bg.secondary,
  borderRadius: 12,
  padding: 20,
  border: `1px solid ${colors.border.subtle}`,
  borderTop: `3px solid ${ACCENT}`,
};

const headerStyle: React.CSSProperties = {
  fontSize: typography.sizes.h3,
  fontWeight: typography.weights.semibold,
  color: ACCENT,
  margin: 0,
};

const labelStyle: React.CSSProperties = {
  fontSize: typography.sizes.small,
  color: colors.text.secondary,
  fontWeight: typography.weights.medium,
  marginBottom: 6,
  marginTop: 0,
};

const emptyStyle: React.CSSProperties = {
  color: colors.text.muted,
  fontSize: typography.sizes.small,
};

const chipStyle: React.CSSProperties = {
  fontSize: typography.sizes.xs,
  color: colors.text.secondary,
  backgroundColor: colors.bg.primary,
  padding: '3px 8px',
  borderRadius: 12,
  border: `1px solid ${colors.border.subtle}`,
};

const actionRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '6px 8px',
  marginBottom: 4,
  backgroundColor: colors.bg.primary,
  borderRadius: 6,
};

const thoughtRowStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  padding: '4px 0',
  borderBottom: `1px solid ${colors.border.subtle}`,
};

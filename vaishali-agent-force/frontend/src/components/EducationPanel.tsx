import React from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { AgentAvatar, deriveAgentState } from './AgentAvatar';

interface EducationPanelProps {
  data: any;
}

export function EducationPanel({ data }: EducationPanelProps) {
  const accent = colors.accent.education;

  return (
    <div style={panelStyle(accent)}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <AgentAvatar agent="education" state={deriveAgentState('education', data)} size={36} />
        <h3 style={{ ...headerStyle(accent), margin: 0 }}>Education & Research</h3>
      </div>

      {!data ? (
        <p style={emptyStyle}>No education data today</p>
      ) : (
        <>
          <div style={metricRow}>
            <span style={labelStyle}>Items Processed</span>
            <span style={{ fontSize: typography.sizes.h2, fontWeight: typography.weights.bold, color: accent }}>
              {data.items_processed ?? 0}
            </span>
          </div>

          {data.top_topics?.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <p style={{ ...labelStyle, marginBottom: 6 }}>Top Topics</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {data.top_topics.slice(0, 8).map((topic: string, i: number) => (
                  <span key={i} style={{
                    padding: '4px 10px',
                    backgroundColor: colors.bg.primary,
                    borderRadius: 12,
                    fontSize: typography.sizes.small,
                    color: accent,
                    border: `1px solid ${accent}33`,
                  }}>
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {data.new_insights?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <p style={{ ...labelStyle, marginBottom: 6 }}>Insights</p>
              {data.new_insights.slice(0, 3).map((insight: string, i: number) => (
                <p key={i} style={{
                  margin: '6px 0',
                  fontSize: typography.sizes.small,
                  color: colors.text.secondary,
                  lineHeight: 1.4,
                }}>
                  {insight.length > 120 ? insight.slice(0, 120) + '...' : insight}
                </p>
              ))}
            </div>
          )}

          {data.next_actions?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <p style={{ ...labelStyle, marginBottom: 6 }}>Next Actions</p>
              {data.next_actions.map((action: string, i: number) => (
                <p key={i} style={{
                  margin: '4px 0',
                  fontSize: typography.sizes.small,
                  color: colors.accent.teal,
                }}>
                  {action}
                </p>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

const panelStyle = (accent: string): React.CSSProperties => ({
  backgroundColor: colors.bg.secondary,
  borderRadius: 12,
  padding: 20,
  border: `1px solid ${colors.border.subtle}`,
  borderTop: `3px solid ${accent}`,
});

const headerStyle = (accent: string): React.CSSProperties => ({
  fontSize: typography.sizes.h3,
  fontWeight: typography.weights.semibold,
  color: accent,
  margin: '0 0 16px',
});

const metricRow: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: 8,
};

const labelStyle: React.CSSProperties = {
  fontSize: typography.sizes.small,
  color: colors.text.secondary,
  fontWeight: typography.weights.medium,
};

const emptyStyle: React.CSSProperties = {
  color: colors.text.muted,
  fontSize: typography.sizes.small,
};

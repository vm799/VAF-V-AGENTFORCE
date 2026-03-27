import React from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { AgentAvatar, deriveAgentState } from './AgentAvatar';

interface ContentPanelProps {
  data: any;
}

export function ContentPanel({ data }: ContentPanelProps) {
  const accent = colors.accent.content;

  return (
    <div style={panelStyle(accent)}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <AgentAvatar agent="content" state={deriveAgentState('content', data)} size={36} />
        <h3 style={{ ...headerStyle(accent), margin: 0 }}>Content</h3>
      </div>

      {!data ? (
        <p style={emptyStyle}>No content data today</p>
      ) : (
        <>
          <div style={metricRow}>
            <span style={labelStyle}>Backlog</span>
            <span style={{ fontSize: typography.sizes.h2, fontWeight: typography.weights.bold, color: accent }}>
              {data.total_backlog ?? 0} items
            </span>
          </div>

          {data.top_ideas?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <p style={{ ...labelStyle, marginBottom: 8 }}>Top Ideas</p>
              {data.top_ideas.map((idea: any, i: number) => (
                <div key={idea.id || i} style={{
                  padding: '8px 10px',
                  backgroundColor: colors.bg.primary,
                  borderRadius: 6,
                  marginBottom: 6,
                }}>
                  <p style={{ margin: 0, fontSize: typography.sizes.body, fontWeight: typography.weights.medium }}>
                    {idea.title}
                  </p>
                  <p style={{ margin: '4px 0 0', fontSize: typography.sizes.small, color: colors.text.muted }}>
                    {idea.type} · {idea.channel} · Effort: {idea.effort} · Impact: {idea.impact}/10
                  </p>
                </div>
              ))}
            </div>
          )}

          {data.drafts_waiting_review?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <p style={{ ...labelStyle, color: colors.status.warning, marginBottom: 6 }}>
                Drafts Waiting Review ({data.drafts_waiting_review.length})
              </p>
              {data.drafts_waiting_review.map((d: any, i: number) => (
                <p key={i} style={{ margin: '4px 0', fontSize: typography.sizes.small }}>
                  {d.title}
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

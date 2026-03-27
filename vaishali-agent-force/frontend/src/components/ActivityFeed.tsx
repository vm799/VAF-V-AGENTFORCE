import React from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';

interface ActivityFeedProps {
  status: any;
}

const agentIcons: Record<string, string> = {
  finance: '💰',
  content: '✍️',
  education: '📚',
  research: '🔬',
  health: '💪',
};

const agentColors: Record<string, string> = {
  finance: colors.accent.finance,
  content: colors.accent.content,
  education: colors.accent.education,
  research: colors.accent.research,
  health: colors.accent.health,
};

export function ActivityFeed({ status }: ActivityFeedProps) {
  const agents = status?.agents ?? {};
  const entries = Object.entries(agents) as [string, any][];

  return (
    <div style={{
      backgroundColor: colors.bg.secondary,
      borderRadius: 12,
      padding: 20,
      border: `1px solid ${colors.border.subtle}`,
    }}>
      <h3 style={{
        fontSize: typography.sizes.h3,
        fontWeight: typography.weights.semibold,
        color: colors.text.primary,
        margin: '0 0 16px',
      }}>
        Agent Status
      </h3>

      {entries.length === 0 ? (
        <p style={{ color: colors.text.muted, fontSize: typography.sizes.small }}>
          No agent data available. Run a briefing to populate.
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {entries.map(([agent, info]) => (
            <div key={agent} style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 12px',
              backgroundColor: colors.bg.primary,
              borderRadius: 8,
              borderLeft: `3px solid ${agentColors[agent] ?? colors.accent.teal}`,
            }}>
              <span style={{ fontSize: '1.2rem' }}>{agentIcons[agent] ?? '📊'}</span>
              <div style={{ flex: 1 }}>
                <p style={{
                  margin: 0,
                  fontSize: typography.sizes.body,
                  fontWeight: typography.weights.medium,
                  color: agentColors[agent] ?? colors.text.primary,
                }}>
                  {agent.charAt(0).toUpperCase() + agent.slice(1)}
                </p>
                <p style={{
                  margin: '2px 0 0',
                  fontSize: typography.sizes.small,
                  color: colors.text.secondary,
                }}>
                  {info?.headline ?? 'No data'}
                </p>
              </div>
              <span style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: info?.has_data ? colors.status.success : colors.text.muted,
                flexShrink: 0,
              }} />
            </div>
          ))}
        </div>
      )}

      <p style={{
        margin: '16px 0 0',
        fontSize: typography.sizes.xs,
        color: colors.text.muted,
        textAlign: 'right',
      }}>
        {status?.date ?? '—'}
      </p>
    </div>
  );
}

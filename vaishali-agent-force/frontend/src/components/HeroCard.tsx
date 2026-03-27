import React from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';

interface HeroCardProps {
  briefing: any;
  loading: boolean;
}

export function HeroCard({ briefing, loading }: HeroCardProps) {
  if (loading) {
    return (
      <div style={cardStyle}>
        <p style={{ color: colors.text.muted }}>Loading briefing...</p>
      </div>
    );
  }

  if (!briefing) {
    return (
      <div style={cardStyle}>
        <p style={{ color: colors.text.secondary }}>
          No briefing yet today. Click "Run Morning" to generate one.
        </p>
      </div>
    );
  }

  return (
    <div style={cardStyle}>
      <div style={{ marginBottom: 16 }}>
        <p style={{
          fontSize: typography.sizes.small,
          color: colors.accent.teal,
          fontWeight: typography.weights.semibold,
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          margin: '0 0 8px',
        }}>
          What Matters Most Today
        </p>
        <h2 style={{
          fontSize: typography.sizes.hero,
          fontWeight: typography.weights.bold,
          color: colors.text.primary,
          margin: 0,
          lineHeight: 1.2,
        }}>
          {briefing.what_matters_most_today}
        </h2>
      </div>

      <div style={{
        padding: '12px 16px',
        backgroundColor: colors.bg.primary,
        borderRadius: 8,
        borderLeft: `3px solid ${colors.accent.teal}`,
      }}>
        <p style={{
          fontSize: typography.sizes.small,
          color: colors.accent.teal,
          fontWeight: typography.weights.medium,
          margin: '0 0 4px',
        }}>
          Today's Win
        </p>
        <p style={{ margin: 0, color: colors.text.primary }}>
          {briefing.todays_win}
        </p>
      </div>

      {briefing.cross_agent_insights?.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <p style={{
            fontSize: typography.sizes.small,
            color: colors.text.secondary,
            fontWeight: typography.weights.medium,
            margin: '0 0 8px',
          }}>
            Cross-Agent Insights
          </p>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {briefing.cross_agent_insights.map((insight: string, i: number) => (
              <li key={i} style={{ color: colors.text.secondary, marginBottom: 4, fontSize: typography.sizes.body }}>
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  backgroundColor: colors.bg.secondary,
  borderRadius: 12,
  padding: 24,
  border: `1px solid ${colors.border.subtle}`,
  marginTop: 20,
};

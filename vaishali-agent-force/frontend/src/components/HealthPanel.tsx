import React from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { AgentAvatar, deriveAgentState } from './AgentAvatar';

interface HealthPanelProps {
  data: any;
}

export function HealthPanel({ data }: HealthPanelProps) {
  const accent = colors.accent.health;

  return (
    <div style={panelStyle(accent)}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <AgentAvatar agent="health" state={deriveAgentState('health', data)} size={36} />
        <h3 style={{ ...headerStyle(accent), margin: 0 }}>Health & Fitness</h3>
      </div>

      {!data || data.body_score == null ? (
        <p style={emptyStyle}>No health data today — log your daily check-in</p>
      ) : (
        <>
          {/* Body Score Ring */}
          <div style={{ textAlign: 'center', marginBottom: 16 }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 80,
              height: 80,
              borderRadius: '50%',
              border: `4px solid ${scoreColor(data.body_score)}`,
              backgroundColor: colors.bg.primary,
            }}>
              <span style={{
                fontSize: typography.sizes.h1,
                fontWeight: typography.weights.bold,
                color: scoreColor(data.body_score),
              }}>
                {data.body_score}
              </span>
            </div>
            <p style={{ margin: '6px 0 0', fontSize: typography.sizes.small, color: colors.text.muted }}>
              Body Score / 10
            </p>
          </div>

          {/* Metrics grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <MetricBox label="Steps" value={data.movement?.steps?.toLocaleString() ?? '—'} sub={`${data.movement?.score ?? 0}/10`} />
            <MetricBox label="Workout" value={`${data.movement?.workout_minutes ?? 0}min`} sub={`${data.movement?.score ?? 0}/10`} />
            <MetricBox label="Sleep" value={`${data.sleep?.hours ?? 0}h`} sub={`${data.sleep?.score ?? 0}/10`} />
            <MetricBox label="Habits" value={`${data.habits?.completed ?? 0}/${data.habits?.total ?? 4}`} sub={`${data.habits?.score ?? 0}/10`} />
          </div>

          {/* Streaks */}
          {data.streaks && (data.streaks.walk_streak > 0 || data.streaks.workout_streak > 0) && (
            <div style={{ marginTop: 12 }}>
              <p style={labelStyle}>Streaks</p>
              {data.streaks.walk_streak > 0 && (
                <p style={{ margin: '4px 0', fontSize: typography.sizes.small, color: colors.status.success }}>
                  {data.streaks.walk_streak}-day walking streak
                </p>
              )}
              {data.streaks.workout_streak > 0 && (
                <p style={{ margin: '4px 0', fontSize: typography.sizes.small, color: colors.status.success }}>
                  {data.streaks.workout_streak}-day workout streak
                </p>
              )}
            </div>
          )}

          {/* Recommendation */}
          {data.recommendation && (
            <div style={{
              marginTop: 12,
              padding: '10px 12px',
              backgroundColor: colors.bg.primary,
              borderRadius: 6,
              borderLeft: `3px solid ${accent}`,
            }}>
              <p style={{ margin: 0, fontSize: typography.sizes.small, color: colors.text.secondary }}>
                {data.recommendation}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MetricBox({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div style={{
      padding: '8px 10px',
      backgroundColor: colors.bg.primary,
      borderRadius: 6,
      textAlign: 'center',
    }}>
      <p style={{ margin: 0, fontSize: typography.sizes.small, color: colors.text.muted }}>{label}</p>
      <p style={{ margin: '2px 0', fontSize: typography.sizes.h3, fontWeight: typography.weights.semibold }}>{value}</p>
      <p style={{ margin: 0, fontSize: typography.sizes.xs, color: colors.text.muted }}>{sub}</p>
    </div>
  );
}

function scoreColor(score: number): string {
  if (score >= 8) return colors.status.success;
  if (score >= 5) return colors.status.warning;
  return colors.status.error;
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

const labelStyle: React.CSSProperties = {
  fontSize: typography.sizes.small,
  color: colors.text.secondary,
  fontWeight: typography.weights.medium,
  marginBottom: 4,
};

const emptyStyle: React.CSSProperties = {
  color: colors.text.muted,
  fontSize: typography.sizes.small,
};

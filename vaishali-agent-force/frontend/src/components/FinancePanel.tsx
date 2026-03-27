import React from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { AgentAvatar, deriveAgentState } from './AgentAvatar';

interface FinancePanelProps {
  data: any;
}

export function FinancePanel({ data }: FinancePanelProps) {
  const accent = colors.accent.finance;

  return (
    <div style={panelStyle(accent)}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <AgentAvatar agent="finance" state={deriveAgentState('finance', data)} size={36} />
        <h3 style={{ ...headerStyle(accent), margin: 0 }}>Finance</h3>
      </div>

      {!data ? (
        <p style={emptyStyle}>No finance data today</p>
      ) : (
        <>
          <div style={metricRow}>
            <span style={labelStyle}>Total Balance</span>
            <span style={{ ...valueStyle, color: accent }}>
              £{(data.total_balance_gbp ?? 0).toLocaleString('en-GB', { minimumFractionDigits: 2 })}
            </span>
          </div>

          {data.accounts?.map((a: any) => (
            <div key={a.id} style={{ ...metricRow, borderTop: `1px solid ${colors.border.subtle}`, paddingTop: 8 }}>
              <div>
                <p style={{ margin: 0, fontSize: typography.sizes.small, color: colors.text.secondary }}>{a.id}</p>
                <p style={{ margin: '2px 0 0', fontWeight: typography.weights.medium }}>
                  £{(a.balance ?? 0).toLocaleString('en-GB', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <p style={{ margin: 0, fontSize: typography.sizes.small, color: colors.text.muted }}>7d</p>
                <p style={{
                  margin: '2px 0 0',
                  color: (a.net_7d ?? 0) >= 0 ? colors.status.success : colors.status.error,
                  fontWeight: typography.weights.medium,
                }}>
                  £{(a.net_7d ?? 0) >= 0 ? '+' : ''}{(a.net_7d ?? 0).toLocaleString('en-GB', { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          ))}

          {data.anomalies?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <p style={{ ...labelStyle, marginBottom: 6 }}>Anomalies ({data.anomalies.length})</p>
              {data.anomalies.slice(0, 3).map((a: any, i: number) => (
                <p key={i} style={{
                  margin: '4px 0',
                  fontSize: typography.sizes.small,
                  color: colors.status.warning,
                }}>
                  {a.description} — £{Math.abs(a.amount).toFixed(2)}
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

const valueStyle: React.CSSProperties = {
  fontSize: typography.sizes.h2,
  fontWeight: typography.weights.bold,
};

const emptyStyle: React.CSSProperties = {
  color: colors.text.muted,
  fontSize: typography.sizes.small,
};

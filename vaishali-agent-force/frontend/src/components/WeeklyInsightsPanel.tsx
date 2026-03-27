import React, { useEffect, useState, useCallback } from 'react';
import { colors } from '../theme/colors';

const GOLD = '#c9a84c';
const TEAL = '#2dd4bf';

interface Theme { theme: string; count: number; agents: string[] }
interface MustAct { agent: string; title: string; signal: string; created_at: string; revenue_angle: string }
interface Connection { topic: string; agents: string[]; capture_count: number; insight: string }
interface ContentIdea { hook: string; platform: string; from_agent: string }
interface RevenueOp { agent: string; title: string; angle: string; signal: string }
interface Goggins { avg_score: number; best_day: string; best_score: number; days_checked: number; streak: number }

interface WeeklyData {
  period: string;
  total_captures: number;
  enriched_count: number;
  must_act: MustAct[];
  by_agent: Record<string, number>;
  top_themes: Theme[];
  revenue_opportunities: RevenueOp[];
  cross_agent_connections: Connection[];
  goggins: Goggins;
  content_ideas: ContentIdea[];
}

const AGENT_COLOR: Record<string, string> = {
  SENTINEL: '#c9a84c', FORGE: '#2dd4bf', AMPLIFY: '#a78bfa', PHOENIX: '#fb923c',
  VITALITY: '#4ade80', CIPHER: '#60a5fa', AEGIS: '#f87171', NEXUS: '#e879f9',
  ATLAS: '#fbbf24', COLOSSUS: '#ef4444',
};

export function WeeklyInsightsPanel() {
  const [data, setData] = useState<WeeklyData | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const res = await fetch('/api/insights/weekly?days=7');
      if (res.ok) setData(await res.json());
    } catch {}
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    load();
    const iv = setInterval(load, 60_000);
    return () => clearInterval(iv);
  }, [load]);

  if (loading) return (
    <div style={cardStyle}>
      <div style={headerStyle}>📊 Weekly Intelligence</div>
      <div style={{ color: colors.text.muted, fontSize: 12 }}>Loading weekly insights…</div>
    </div>
  );

  if (!data || data.total_captures === 0) return (
    <div style={cardStyle}>
      <div style={headerStyle}>📊 Weekly Intelligence</div>
      <div style={{ color: colors.text.secondary, fontSize: 12 }}>
        No captures this week yet. Drop thoughts, URLs, and ideas via Telegram <code style={{ color: TEAL }}>/save</code> to see weekly patterns here.
      </div>
    </div>
  );

  return (
    <div style={cardStyle}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <div style={headerStyle}>📊 Weekly Intelligence</div>
          <div style={{ color: colors.text.muted, fontSize: 11 }}>{data.period}</div>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          {[
            { n: data.total_captures, l: 'captures', c: GOLD },
            { n: data.enriched_count, l: 'enriched', c: TEAL },
            { n: data.must_act.length, l: 'must-act', c: '#4ade80' },
          ].map(s => (
            <div key={s.l} style={{ textAlign: 'center' }}>
              <div style={{ color: s.c, fontSize: 18, fontWeight: 800 }}>{s.n}</div>
              <div style={{ color: colors.text.muted, fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' as const }}>{s.l}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Must-Act */}
        {data.must_act.length > 0 && (
          <div style={sectionStyle('#4ade80')}>
            <div style={sectionLabel}>🟢 Must-Act This Week</div>
            {data.must_act.map((item, i) => (
              <div key={i} style={{ padding: '6px 0', borderBottom: i < data.must_act.length - 1 ? `1px solid ${colors.border.subtle}` : 'none' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ ...agentPill, color: AGENT_COLOR[item.agent] || '#888' }}>{item.agent}</span>
                  <span style={{ fontSize: 11, color: colors.text.primary, fontWeight: 500 }}>{item.title}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Top Themes */}
        {data.top_themes.length > 0 && (
          <div style={sectionStyle(GOLD)}>
            <div style={sectionLabel}>🔥 Top Themes</div>
            {data.top_themes.slice(0, 6).map((t, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '5px 0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: colors.text.primary }}>{t.theme}</span>
                  <span style={{ fontSize: 10, color: colors.text.muted }}>{t.count}×</span>
                </div>
                <div style={{ display: 'flex', gap: 3 }}>
                  {t.agents.map(a => (
                    <span key={a} style={{ fontSize: 9, color: AGENT_COLOR[a] || '#888', background: `${AGENT_COLOR[a] || '#888'}15`,
                      border: `1px solid ${AGENT_COLOR[a] || '#888'}30`, borderRadius: 3, padding: '0 4px' }}>{a}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Cross-Agent Connections */}
        {data.cross_agent_connections.length > 0 && (
          <div style={sectionStyle('#e879f9')}>
            <div style={sectionLabel}>🔗 Cross-Agent Connections</div>
            {data.cross_agent_connections.slice(0, 3).map((conn, i) => (
              <div key={i} style={{ padding: '6px 0', fontSize: 11, color: colors.text.secondary, lineHeight: 1.5 }}>
                {conn.insight}
              </div>
            ))}
          </div>
        )}

        {/* Content Ideas */}
        {data.content_ideas.length > 0 && (
          <div style={sectionStyle('#a78bfa')}>
            <div style={sectionLabel}>📱 Content Ideas (AMPLIFY)</div>
            {data.content_ideas.slice(0, 3).map((idea, i) => (
              <div key={i} style={{ padding: '6px 0', borderBottom: i < 2 ? `1px solid ${colors.border.subtle}` : 'none' }}>
                <div style={{ fontSize: 11, color: colors.text.primary, fontWeight: 500 }}>{idea.hook}</div>
                <div style={{ fontSize: 10, color: colors.text.muted, marginTop: 2 }}>
                  {idea.platform} · from {idea.from_agent}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Goggins row */}
      {data.goggins.days_checked > 0 && (
        <div style={{
          marginTop: 16, padding: '12px 16px', background: 'rgba(224,92,92,0.06)',
          border: '1px solid rgba(224,92,92,0.15)', borderRadius: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 18 }}>🔥</span>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: colors.text.primary }}>Goggins Protocol</div>
              <div style={{ fontSize: 10, color: colors.text.muted }}>
                {data.goggins.days_checked} days checked in · streak: {data.goggins.streak}d
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: GOLD }}>{data.goggins.avg_score}</div>
              <div style={{ fontSize: 9, color: colors.text.muted, letterSpacing: '0.06em' }}>AVG/50</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#4ade80' }}>{data.goggins.best_score}</div>
              <div style={{ fontSize: 9, color: colors.text.muted, letterSpacing: '0.06em' }}>BEST</div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{
        marginTop: 14, fontSize: 10, color: colors.text.muted, textAlign: 'center',
      }}>
        💡 Telegram: <code style={{ color: TEAL }}>/weekly</code> for full brief · updates every 60s
      </div>
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  background: colors.bg.secondary, border: `1px solid ${colors.border.default}`,
  borderRadius: 12, padding: '20px 24px', marginBottom: 24,
};

const headerStyle: React.CSSProperties = {
  color: GOLD, fontSize: 14, fontWeight: 700, letterSpacing: '0.05em',
};

const sectionStyle = (accentColor: string): React.CSSProperties => ({
  background: `${accentColor}06`, border: `1px solid ${accentColor}18`,
  borderRadius: 8, padding: '12px 14px',
});

const sectionLabel: React.CSSProperties = {
  fontSize: 10, fontWeight: 700, color: colors.text.muted,
  letterSpacing: '0.08em', textTransform: 'uppercase',
  marginBottom: 8, paddingBottom: 6, borderBottom: `1px solid ${colors.border.subtle}`,
};

const agentPill: React.CSSProperties = {
  fontSize: 9, fontWeight: 700, letterSpacing: '0.06em',
  background: 'rgba(255,255,255,0.05)', borderRadius: 3,
  padding: '1px 5px',
};

import React, { useEffect, useState, useCallback } from 'react';
import { colors } from '../theme/colors';

// ── Types ──────────────────────────────────────────────────────────────────────

interface DayCheckin {
  id: number;
  checkin_date: string;
  total: number;
  scores: Record<string, number>;
  note?: string;
  created_at: string;
}

interface CheckinsData {
  streak: number;
  avg_total: number;
  best_total: number;
  completion_rate: number;
  by_negotiable: Record<string, { avg: number; best: number }>;
  checkins: DayCheckin[];
}

// ── Constants ─────────────────────────────────────────────────────────────────

const GOLD = '#c9a84c';
const TEAL = colors.accent.teal;

const NON_NEGOTIABLES = ['BODY', 'BUILD', 'LEARN', 'AMPLIFY', 'BRIEF'] as const;

const NN_META: Record<string, { emoji: string; label: string; color: string }> = {
  BODY:    { emoji: '🔥', label: '5×5 Physical',   color: '#f87171' },
  BUILD:   { emoji: '🏗️', label: 'Ship to Prod',   color: TEAL },
  LEARN:   { emoji: '🧠', label: 'AWS + CIPHER',   color: '#60a5fa' },
  AMPLIFY: { emoji: '📱', label: 'Content Created', color: '#a78bfa' },
  BRIEF:   { emoji: '📋', label: 'Brief + Debrief', color: GOLD },
};

function scoreColor(score: number): string {
  if (score >= 8) return '#4ade80';
  if (score >= 5) return GOLD;
  if (score >= 3) return '#fb923c';
  return '#f87171';
}

function totalColor(total: number): string {
  if (total >= 45) return '#4ade80';
  if (total >= 35) return GOLD;
  if (total >= 25) return '#fb923c';
  return '#f87171';
}

function gogginsFeedback(total: number): string {
  if (total === 50) return "🔥 PERFECT DAY. That's carrying the boats.";
  if (total >= 45) return '💪 Almost perfect. What did you miss?';
  if (total >= 35) return '✅ Solid. But you left something in the tank.';
  if (total >= 25) return "⚠️ Survived. That's not the same as winning.";
  if (total >= 15) return "🛑 Soft day. Non-negotiables aren't optional.";
  return '🚨 You got outworked. Use that feeling. Tomorrow is war.';
}

// ── Heatmap cell ──────────────────────────────────────────────────────────────

function HeatCell({ date, total, isToday }: { date: string; total: number | null; isToday: boolean }) {
  const bg = total === null
    ? 'rgba(255,255,255,0.04)'
    : total >= 45 ? 'rgba(74,222,128,0.85)'
    : total >= 35 ? 'rgba(201,168,76,0.85)'
    : total >= 25 ? 'rgba(251,146,60,0.7)'
    : 'rgba(248,113,113,0.6)';

  const label = date.slice(5); // MM-DD

  return (
    <div
      title={total !== null ? `${label}: ${total}/50` : label}
      style={{
        width: 22,
        height: 22,
        borderRadius: 4,
        background: bg,
        border: isToday ? `2px solid ${TEAL}` : '1px solid transparent',
        flexShrink: 0,
        cursor: total !== null ? 'pointer' : 'default',
        transition: 'transform 0.1s',
      }}
    />
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export function AccountabilityPanel() {
  const [data, setData]       = useState<CheckinsData | null>(null);
  const [today, setToday]     = useState<DayCheckin | null>(null);
  const [streak, setStreak]   = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [statsRes, todayRes] = await Promise.all([
        fetch('/api/checkins?limit=30'),
        fetch('/api/checkins/today'),
      ]);
      if (statsRes.ok) setData(await statsRes.json());
      if (todayRes.ok) {
        const td = await todayRes.json();
        setToday(td.checkin ?? null);
        setStreak(td.streak ?? 0);
      }
    } catch (_) {
      // API may not be running yet
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const iv = setInterval(load, 60_000);
    window.addEventListener('focus', load);
    return () => { clearInterval(iv); window.removeEventListener('focus', load); };
  }, [load]);

  // Build a 30-day date grid
  const todayStr = new Date().toISOString().slice(0, 10);
  const last30: string[] = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    last30.push(d.toISOString().slice(0, 10));
  }
  const scoreByDate: Record<string, number> = {};
  (data?.checkins ?? []).forEach(c => { scoreByDate[c.checkin_date] = c.total; });

  return (
    <div style={{
      background: colors.bg.secondary,
      border: `1px solid ${colors.border.default}`,
      borderRadius: 12,
      padding: '20px 24px',
      marginBottom: 24,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 22 }}>🔥</span>
          <div>
            <div style={{ color: GOLD, fontSize: 14, fontWeight: 700, letterSpacing: '0.05em' }}>
              GOGGINS NON-NEGOTIABLES
            </div>
            <div style={{ color: colors.text.secondary, fontSize: 12, marginTop: 2 }}>
              Daily accountability · 5 pillars · 50 pts max
            </div>
          </div>
        </div>
        {/* Streak badge */}
        <div style={{
          background: streak > 0 ? 'rgba(248,113,113,0.15)' : 'rgba(255,255,255,0.04)',
          border: `1px solid ${streak > 0 ? 'rgba(248,113,113,0.4)' : colors.border.subtle}`,
          borderRadius: 8,
          padding: '6px 14px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: 18, lineHeight: 1 }}>🔥</div>
          <div style={{ color: streak > 0 ? '#f87171' : colors.text.muted, fontSize: 16, fontWeight: 800 }}>
            {streak}
          </div>
          <div style={{ color: colors.text.muted, fontSize: 9, letterSpacing: '0.05em' }}>STREAK</div>
        </div>
      </div>

      {/* Today's scores */}
      {today ? (
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          borderRadius: 8,
          padding: '14px 16px',
          marginBottom: 16,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <span style={{ color: colors.text.primary, fontSize: 12, fontWeight: 700 }}>TODAY</span>
            <span style={{
              color: totalColor(today.total),
              fontSize: 16,
              fontWeight: 800,
            }}>
              {today.total}/50
            </span>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {NON_NEGOTIABLES.map(k => {
              const v = today.scores[k] ?? 0;
              const meta = NN_META[k];
              return (
                <div key={k} style={{
                  flex: '1 0 80px',
                  background: `rgba(255,255,255,0.04)`,
                  borderRadius: 6,
                  padding: '8px 10px',
                  border: `1px solid ${meta.color}30`,
                  textAlign: 'center',
                }}>
                  <div style={{ fontSize: 16, marginBottom: 4 }}>{meta.emoji}</div>
                  <div style={{
                    fontSize: 18,
                    fontWeight: 800,
                    color: scoreColor(v),
                    lineHeight: 1,
                  }}>{v}</div>
                  <div style={{
                    fontSize: 9,
                    color: colors.text.muted,
                    marginTop: 3,
                    letterSpacing: '0.04em',
                  }}>{k}</div>
                </div>
              );
            })}
          </div>
          <div style={{
            marginTop: 10,
            fontSize: 11,
            color: totalColor(today.total),
            fontStyle: 'italic',
          }}>
            {gogginsFeedback(today.total)}
          </div>
        </div>
      ) : !loading && (
        <div style={{
          background: 'rgba(248,113,113,0.06)',
          border: '1px solid rgba(248,113,113,0.2)',
          borderRadius: 8,
          padding: '14px 16px',
          marginBottom: 16,
          textAlign: 'center',
        }}>
          <div style={{ color: '#f87171', fontWeight: 700, fontSize: 13, marginBottom: 6 }}>
            🚨 No check-in today
          </div>
          <div style={{ color: colors.text.secondary, fontSize: 11, lineHeight: 1.7 }}>
            Score your non-negotiables now:<br />
            <code style={{ color: TEAL, background: 'rgba(45,212,191,0.1)', padding: '2px 8px', borderRadius: 4 }}>
              /checkin 8 10 7 6 9
            </code>
          </div>
          <div style={{ color: colors.text.muted, fontSize: 10, marginTop: 6 }}>
            Order: 🔥BODY · 🏗️BUILD · 🧠LEARN · 📱AMPLIFY · 📋BRIEF
          </div>
        </div>
      )}

      {/* Stats row */}
      {data && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 8,
          marginBottom: 16,
        }}>
          {[
            { label: 'AVG / DAY', value: `${data.avg_total}/50`, color: TEAL },
            { label: 'BEST DAY', value: `${data.best_total}/50`, color: '#4ade80' },
            { label: 'COMPLETION', value: `${data.completion_rate}%`, color: GOLD },
          ].map(s => (
            <div key={s.label} style={{
              background: 'rgba(255,255,255,0.03)',
              border: `1px solid ${colors.border.subtle}`,
              borderRadius: 6,
              padding: '8px 10px',
              textAlign: 'center',
            }}>
              <div style={{ color: s.color, fontSize: 16, fontWeight: 800 }}>{s.value}</div>
              <div style={{ color: colors.text.muted, fontSize: 9, letterSpacing: '0.06em', marginTop: 2 }}>
                {s.label}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 30-day heatmap */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ color: colors.text.muted, fontSize: 10, marginBottom: 6, letterSpacing: '0.05em' }}>
          30-DAY HEATMAP
        </div>
        <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          {last30.map(d => (
            <HeatCell
              key={d}
              date={d}
              total={d in scoreByDate ? scoreByDate[d] : null}
              isToday={d === todayStr}
            />
          ))}
        </div>
        <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
          {[
            { color: 'rgba(74,222,128,0.85)', label: '45–50 Elite' },
            { color: 'rgba(201,168,76,0.85)', label: '35–44 Solid' },
            { color: 'rgba(251,146,60,0.7)',  label: '25–34 Streak' },
            { color: 'rgba(248,113,113,0.6)', label: '<25 Miss' },
          ].map(l => (
            <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: l.color }} />
              <span style={{ color: colors.text.muted, fontSize: 9 }}>{l.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Per-negotiable averages */}
      {data?.by_negotiable && (
        <div style={{ marginTop: 14 }}>
          <div style={{ color: colors.text.muted, fontSize: 10, marginBottom: 8, letterSpacing: '0.05em' }}>
            30-DAY AVERAGES
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {NON_NEGOTIABLES.map(k => {
              const meta = NN_META[k];
              const avg = data.by_negotiable[k]?.avg ?? 0;
              const pct = (avg / 10) * 100;
              return (
                <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 13, width: 20 }}>{meta.emoji}</span>
                  <span style={{ color: colors.text.secondary, fontSize: 11, width: 68, flexShrink: 0 }}>
                    {k}
                  </span>
                  <div style={{ flex: 1, background: 'rgba(255,255,255,0.06)', borderRadius: 3, height: 6 }}>
                    <div style={{
                      width: `${pct}%`,
                      height: '100%',
                      background: meta.color,
                      borderRadius: 3,
                      transition: 'width 0.4s ease',
                    }} />
                  </div>
                  <span style={{ color: meta.color, fontSize: 11, fontWeight: 700, width: 28, textAlign: 'right' }}>
                    {avg.toFixed(1)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Footer hint */}
      <div style={{
        marginTop: 16,
        padding: '8px 12px',
        background: 'rgba(45,212,191,0.04)',
        border: '1px solid rgba(45,212,191,0.1)',
        borderRadius: 6,
        fontSize: 10,
        color: colors.text.muted,
      }}>
        💡 Log via Telegram: <code style={{ color: TEAL }}>/checkin [BODY] [BUILD] [LEARN] [AMPLIFY] [BRIEF]</code>
        &nbsp;·&nbsp;
        <code style={{ color: TEAL }}>/nonneg</code> to see scoring guide
      </div>
    </div>
  );
}

import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { HeroCard } from './components/HeroCard';
import { FinancePanel } from './components/FinancePanel';
import { ContentPanel } from './components/ContentPanel';
import { EducationPanel } from './components/EducationPanel';
import { HealthPanel } from './components/HealthPanel';
import { ActivityFeed } from './components/ActivityFeed';
import { KnowledgeGraph } from './components/KnowledgeGraph';
import { AgentStrip } from './components/AgentStrip';
import { BraindumpPanel } from './components/BraindumpPanel';
import { ReportsPanel } from './components/ReportsPanel';
import { InsightsPanel } from './components/InsightsPanel';
import { WeeklyInsightsPanel } from './components/WeeklyInsightsPanel';
import { UrlQueuePanel } from './components/UrlQueuePanel';
import { CapturesPanel } from './components/CapturesPanel';
import { AccountabilityPanel } from './components/AccountabilityPanel';
import { PixelAgentsCanvas } from './components/PixelAgentsCanvas';
import { colors } from './theme/colors';
import { typography } from './theme/typography';

const API_BASE = '/api';

async function fetchJson(path: string) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) return null;
  return res.json();
}

export function App() {
  const [briefing, setBriefing] = useState<any>(null);
  const [finance, setFinance] = useState<any>(null);
  const [content, setContent] = useState<any>(null);
  const [education, setEducation] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [graph, setGraph] = useState<any>(null);
  const [status, setStatus] = useState<any>(null);
  const [braindump, setBraindump] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    setLoading(true);
    const [b, f, c, e, h, g, s, bd] = await Promise.all([
      fetchJson('/briefings/today'),
      fetchJson('/finance/summary/today'),
      fetchJson('/content/summary/today'),
      fetchJson('/education/summary/today'),
      fetchJson('/health/summary/today'),
      fetchJson('/graph'),
      fetchJson('/status'),
      fetchJson('/braindump/summary/today'),
    ]);
    setBriefing(b);
    setFinance(f);
    setContent(c);
    setEducation(e);
    setHealth(h);
    setGraph(g);
    setStatus(s);
    setBraindump(bd);
    setLoading(false);
  };

  useEffect(() => {
    refresh();
    // Auto-refresh all agent summaries every 30 seconds
    const interval = setInterval(refresh, 30_000);
    // Also refresh when tab gets focus (user comes back after checking Telegram)
    window.addEventListener('focus', refresh);
    return () => { clearInterval(interval); window.removeEventListener('focus', refresh); };
  }, []);

  const runCommand = async (cmd: string) => {
    await fetch(`${API_BASE}/commands/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd }),
    });
    setTimeout(refresh, 2000);
  };

  const speakBriefing = async () => {
    await fetch(`${API_BASE}/briefings/speak`, { method: 'POST' });
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: colors.bg.primary,
      color: colors.text.primary,
      fontFamily: typography.fontFamily,
      fontSize: typography.sizes.body,
    }}>
      <Header
        onRunMorning={() => runCommand('morning')}
        onRunEvening={() => runCommand('evening')}
        onWhereAreWe={() => runCommand('where_are_we')}
        onSpeak={speakBriefing}
        onRefresh={refresh}
      />

      <main style={{ maxWidth: 1400, margin: '0 auto', padding: '0 24px 48px' }}>
        <AgentStrip finance={finance} content={content} education={education} health={health} />
        <HeroCard briefing={briefing} loading={loading} />

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: 20,
          marginTop: 20,
        }}>
          <FinancePanel data={finance} />
          <ContentPanel data={content} />
          <EducationPanel data={education} />
          <HealthPanel data={health} />
          <BraindumpPanel data={braindump} />
        </div>

        {/* Knowledge Graph — full width */}
        <div style={{ marginTop: 20 }}>
          <KnowledgeGraph data={graph} />
        </div>

        {/* Activity Feed */}
        <div style={{ marginTop: 20 }}>
          <ActivityFeed status={status} />
        </div>

        {/* Saved Links / URL Queue — full width */}
        <div style={{ marginTop: 20 }}>
          <UrlQueuePanel />
        </div>

        {/* Accountability Panel — Goggins Non-Negotiables + streak */}
        <div style={{ marginTop: 20 }}>
          <AccountabilityPanel />
        </div>

        {/* Weekly Intelligence — patterns, themes, cross-agent connections */}
        <div style={{ marginTop: 20 }}>
          <WeeklyInsightsPanel />
        </div>

        {/* Captures Panel — intelligence drops from Claude Project */}
        <div style={{ marginTop: 20 }}>
          <CapturesPanel />
        </div>

        {/* Insights Panel — URL-extracted insights */}
        <div style={{ marginTop: 20 }}>
          <InsightsPanel />
        </div>

        {/* Reports Panel — full width */}
        <ReportsPanel />
      </main>

      {/* Wandering pixel agents — fixed canvas overlay */}
      <PixelAgentsCanvas wanderZone={0.55} />
    </div>
  );
}

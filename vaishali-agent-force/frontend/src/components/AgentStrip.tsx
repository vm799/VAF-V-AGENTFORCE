/**
 * AgentStrip — Horizontal bar at the top of the dashboard showing all agent
 * mascots with their current status, a one-line "mood", and a status dot.
 *
 * Sits between the Header and HeroCard.
 */
import React from 'react';
import { AgentAvatar, AgentId, AgentState, AGENT_CONFIG, deriveAgentState } from './AgentAvatar';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';

interface AgentStripProps {
  finance: any;
  content: any;
  education: any;
  health: any;
}

/* ── Per-agent mood line derived from data ───────────────────── */

function agentMood(agent: AgentId, data: any): string {
  if (!data) return 'Waiting for data...';

  switch (agent) {
    case 'finance': {
      const anomalies = data.anomalies?.length ?? 0;
      if (anomalies > 0) return `Watching ${anomalies} anomal${anomalies > 1 ? 'ies' : 'y'}`;
      if (data.total_balance_gbp != null) return 'All accounts healthy';
      return 'Standing by';
    }
    case 'content': {
      const drafts = data.drafts_waiting_review?.length ?? 0;
      const ideas = data.top_ideas?.length ?? 0;
      if (drafts > 0) return `${drafts} draft${drafts > 1 ? 's' : ''} ready for review`;
      if (ideas > 0) return `${ideas} fresh idea${ideas > 1 ? 's' : ''} today`;
      return 'Looking for inspiration';
    }
    case 'education': {
      const items = data.items_processed ?? 0;
      if (items > 0) return `Processed ${items} item${items > 1 ? 's' : ''} today`;
      return 'Ready to learn';
    }
    case 'health': {
      if (data.body_score == null) return 'Log your daily check-in';
      if (data.body_score >= 8) return 'Feeling great!';
      if (data.body_score >= 5) return 'Doing okay — keep moving';
      return 'Needs attention today';
    }
  }
}

/* ── Component ───────────────────────────────────────────────── */

const AGENTS: AgentId[] = ['finance', 'content', 'education', 'health'];

export function AgentStrip({ finance, content, education, health }: AgentStripProps) {
  const dataMap: Record<AgentId, any> = { finance, content, education, health };

  return (
    <div style={{
      display: 'flex',
      gap: 12,
      padding: '12px 0',
      overflowX: 'auto',
      scrollbarWidth: 'none',
    }}>
      {AGENTS.map((id) => {
        const data = dataMap[id];
        const state: AgentState = deriveAgentState(id, data);
        const mood = agentMood(id, data);
        const config = AGENT_CONFIG[id];

        return (
          <div key={id} style={{
            flex: '1 1 0',
            minWidth: 140,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 14px',
            backgroundColor: colors.bg.secondary,
            borderRadius: 10,
            border: `1px solid ${colors.border.subtle}`,
            transition: 'border-color 0.2s',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLDivElement).style.borderColor = config.colour + '60';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLDivElement).style.borderColor = colors.border.subtle;
          }}
          >
            <AgentAvatar agent={id} state={state} size={44} />

            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{
                margin: 0,
                fontSize: typography.sizes.small,
                fontWeight: typography.weights.semibold,
                color: config.colour,
              }}>
                {config.name}
              </p>
              <p style={{
                margin: '2px 0 0',
                fontSize: typography.sizes.xs,
                color: colors.text.secondary,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}>
                {mood}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

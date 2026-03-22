import React, { useEffect, useState } from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';

interface HeaderProps {
  onRunMorning: () => void;
  onRunEvening: () => void;
  onWhereAreWe: () => void;
  onSpeak: () => void;
  onRefresh: () => void;
}

export function Header({ onRunMorning, onRunEvening, onWhereAreWe, onSpeak, onRefresh }: HeaderProps) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const btnStyle: React.CSSProperties = {
    padding: '6px 12px',
    borderRadius: 8,
    border: `1px solid ${colors.border.default}`,
    backgroundColor: colors.bg.tertiary,
    color: colors.text.primary,
    fontSize: '12px',
    fontWeight: typography.weights.medium,
    cursor: 'pointer',
    transition: 'background-color 0.2s',
    fontFamily: typography.fontFamily,
    whiteSpace: 'nowrap',
    flexShrink: 0,
  };

  return (
    <header style={{
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      padding: '12px 20px',
      borderBottom: `1px solid ${colors.border.subtle}`,
      backgroundColor: colors.bg.secondary,
      position: 'sticky',
      top: 0,
      zIndex: 100,
      gap: 12,
      flexWrap: 'wrap',
    }}>
      <div style={{ minWidth: 0, flex: '1 1 220px' }}>
        <h1 style={{
          fontSize: typography.sizes.h2,
          fontWeight: typography.weights.bold,
          color: colors.accent.teal,
          margin: 0,
          letterSpacing: '-0.02em',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}>
          Vaishali Command Center
        </h1>
        <p style={{
          fontSize: '11px',
          color: colors.text.secondary,
          margin: '3px 0 0',
          whiteSpace: 'nowrap',
        }}>
          {time.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })}
          {' · '}
          {time.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </p>
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', flex: '0 1 auto' }}>
        <button style={btnStyle} onClick={onRunMorning}>☀️ Morning</button>
        <button style={btnStyle} onClick={onRunEvening}>🌙 Evening</button>
        <button style={btnStyle} onClick={onWhereAreWe}>📍 Where Are We?</button>
        <button style={{ ...btnStyle, backgroundColor: colors.accent.teal, color: colors.text.inverse, border: 'none' }} onClick={onSpeak}>
          🔊 Speak
        </button>
        <button style={btnStyle} onClick={onRefresh}>↻</button>
      </div>
    </header>
  );
}

/**
 * PixelAgentsCanvas v2 — Pokémon-style battles, weapons, cursor interaction
 *
 * Each agent matches their top-bar mascot:
 *   finance  → Owlbert 🦉  (owl, coin blaster)
 *   content  → Foxy 🦊     (fox, pen wand)
 *   education→ Whiskers 🐱 (cat with glasses, book launcher)
 *   health   → Bamboo 🐼   (panda, dumbbell throw)
 *   braindump→ Brain 🧠    (brain head, lightning zap)
 *   research → Sage 🔬     (lab coat, science beam)
 *
 * Features:
 *   - Unique pixel sprites per character type (8×14 grid)
 *   - Pokémon battles when characters meet: HP bars, attack animations,
 *     damage floats, faint & respawn
 *   - Cursor: characters flee when cursor gets close, face cursor when near,
 *     click a character to make it attack toward the cursor
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';

// ── Constants ──────────────────────────────────────────────────────────────
const SCALE = 4;
const SW = 8 * SCALE;    // 32 px sprite width
const SH = 14 * SCALE;   // 56 px sprite height

const BATTLE_RANGE       = 100;   // px — chars this close trigger battle
const BATTLE_HP          = 30;
const ATTACK_INTERVAL    = 90;    // ticks between attacks
const PROJ_SPEED         = 5;     // projectile px/tick

const CURSOR_FLEE_RANGE  = 75;    // px — flee from cursor
const CURSOR_AWARE_RANGE = 150;   // px — look at cursor

const WALK_SPEED         = 0.7;
const WALK_SPEED_ANXIOUS = 1.5;
const WALK_SPEED_FLEE    = 2.8;

const ANIM_WALK_RATE     = 14;
const DIR_CHANGE_MIN     = 90;
const DIR_CHANGE_MAX     = 240;
const SPEECH_DURATION    = 160;
const SPEECH_CHANCE      = 0.0025;
const FAINT_DURATION     = 280;   // ticks until respawn after faint
const HIT_FLASH_DURATION = 8;

// ── Sprite art (8 cols × 14 rows) ─────────────────────────────────────────
// Color key (meaning varies per agent — see colors map in AGENTS):
//   . = transparent   H = main head/body   D = dark accent
//   L = light/face    O = eye              M = mouth/nose
//   B = shirt/coat    T = pants/legs       E = feet/paws
//   W = weapon hand   G = glasses          X = special mark

// frame indices: 0=stand, 1=walkA, 2=walkB, 3=attack

const OWL: string[][] = [
  // stand
  ['..DD....', '.HHHHHH.', '.HHHHHH.', '.LOOLLL.', '.LMMLLL.',
   '..HHHH..', 'WBBBBB..', '.BBBBB..', '.BBBBB..', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', 'EE....EE', '........'],
  // walkA
  ['..DD....', '.HHHHHH.', '.HHHHHH.', '.LOOLLL.', '.LMMLLL.',
   '..HHHH..', 'WBBBBB..', '.BBBBB..', '.BB.BB..', '.TTT.T..',
   '.TTT.T..', '.EEE.E..', 'EEEE..E.', '........'],
  // walkB
  ['..DD....', '.HHHHHH.', '.HHHHHH.', '.LOOLLL.', '.LMMLLL.',
   '..HHHH..', 'WBBBBB..', '.BBBBB..', '.BB.BB..', '.T.TTT..',
   '.T.TTT..', '.E.EEE..', 'E...EEEE', '........'],
  // attack
  ['..DD....', '.HHHHHH.', '.HHHHHH.', '.LOOLLL.', '.LMMLLL.',
   '..HHHH..', 'WBBBBBW.', '.BBBBB..', '.BBBBB..', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', 'EE....EE', '........'],
];

const FOX: string[][] = [
  // stand
  ['.D....D.', '.HH..HH.', '.HHHHHH.', '.HLLLHH.', '.LOOLLH.',
   '.LMMLLL.', 'WBBBBH..', '.BBBBHH.', '.BBBHHH.', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', '.EE..EE.', '........'],
  // walkA
  ['.D....D.', '.HH..HH.', '.HHHHHH.', '.HLLLHH.', '.LOOLLH.',
   '.LMMLLL.', 'WBBBBH..', '.BBBBHH.', '.BB.BHH.', '.TTT.TH.',
   '.TTT.TH.', '.EEE.E..', 'EEEE..E.', '........'],
  // walkB
  ['.D....D.', '.HH..HH.', '.HHHHHH.', '.HLLLHH.', '.LOOLLH.',
   '.LMMLLL.', 'WBBBBH..', '.BBBBHH.', '.BB.BHH.', '.T.TTTH.',
   '.T.TTTH.', '.E.EEE..', 'E...EEEE', '........'],
  // attack
  ['.D....D.', '.HH..HH.', '.HHHHHH.', '.HLLLHH.', '.LOOLLH.',
   '.LMMLLL.', 'WBBBBHW.', '.BBBBHH.', '.BBBHHH.', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', '.EE..EE.', '........'],
];

const CAT: string[][] = [
  // stand
  ['D......D', '.HH..HH.', '.HHHHHH.', '.HGGGGH.', '.GGOGGO.',
   '.HMLLLH.', 'WBBBBBB.', '.BBBBBB.', '.BBBBBB.', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', '.EE..EE.', '........'],
  // walkA
  ['D......D', '.HH..HH.', '.HHHHHH.', '.HGGGGH.', '.GGOGGO.',
   '.HMLLLH.', 'WBBBBBB.', '.BBBBBB.', '.BB.BBB.', '.TTT.TT.',
   '.TTT.TT.', '.EEE.E..', 'EEEE..E.', '........'],
  // walkB
  ['D......D', '.HH..HH.', '.HHHHHH.', '.HGGGGH.', '.GGOGGO.',
   '.HMLLLH.', 'WBBBBBB.', '.BBBBBB.', '.BB.BBB.', '.TT.TTT.',
   '.TT.TTT.', '.E.EEEE.', 'E...EEE.', '........'],
  // attack
  ['D......D', '.HH..HH.', '.HHHHHH.', '.HGGGGH.', '.GGOGGO.',
   '.HMLLLH.', 'WBBBBBBW', '.BBBBBB.', '.BBBBBB.', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', '.EE..EE.', '........'],
];

const PANDA: string[][] = [
  // stand
  ['D......D', 'DHHHHHDD', '.HHHHHH.', '.XHOOHX.', '.XHHX...', // X=eye patch
   '.HMMMHH.', 'WBBBBBB.', '.BBBBBB.', '.BBBBBB.', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', '.EE..EE.', '........'],
  // walkA
  ['D......D', 'DHHHHHDD', '.HHHHHH.', '.XHOOHX.', '.XHHX...',
   '.HMMMHH.', 'WBBBBBB.', '.BBBBBB.', '.BB.BBB.', '.TTT.TT.',
   '.TTT.TT.', '.EEE.E..', 'EEEE..E.', '........'],
  // walkB
  ['D......D', 'DHHHHHDD', '.HHHHHH.', '.XHOOHX.', '.XHHX...',
   '.HMMMHH.', 'WBBBBBB.', '.BBBBBB.', '.BB.BBB.', '.TT.TTT.',
   '.TT.TTT.', '.E.EEE..', 'E...EEE.', '........'],
  // attack
  ['D......D', 'DHHHHHDD', '.HHHHHH.', '.XHOOHX.', '.XHHX...',
   '.HMMMHH.', 'WBBBBBBW', '.BBBBBB.', '.BBBBBB.', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', '.EE..EE.', '........'],
];

const BRAIN: string[][] = [
  // stand — lumpy brain-shaped head
  ['HHHHHHHH', '.HHHHHH.', '.HLLLLH.', '.LOOOLH.', '.LLMLL..',
   '........', 'WBBBBB..', '.BBBBB..', '.BBBBB..', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', '.EE..EE.', '........'],
  // walkA
  ['HHHHHHHH', '.HHHHHH.', '.HLLLLH.', '.LOOOLH.', '.LLMLL..',
   '........', 'WBBBBB..', '.BBBBB..', '.BB.BB..', '.TTT.T..',
   '.TTT.T..', '.EEE.E..', 'EEEE..E.', '........'],
  // walkB
  ['HHHHHHHH', '.HHHHHH.', '.HLLLLH.', '.LOOOLH.', '.LLMLL..',
   '........', 'WBBBBB..', '.BBBBB..', '.BB.BB..', '.T.TTT..',
   '.T.TTT..', '.E.EEE..', 'E...EEEE', '........'],
  // attack
  ['HHHHHHHH', '.HHHHHH.', '.HLLLLH.', '.LOOOLH.', '.LLMLL..',
   '........', 'WBBBBBW.', '.BBBBB..', '.BBBBB..', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', '.EE..EE.', '........'],
];

const SAGE: string[][] = [
  // stand — lab coat
  ['..DDDD..', '.HHHHHH.', '.HHHHHH.', '.LOOLHH.', '.LMMLHH.',
   '..HHHH..', 'WBBBBBB.', 'BBBBBBB.', 'BBBBBBB.', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', '.EE..EE.', '........'],
  // walkA
  ['..DDDD..', '.HHHHHH.', '.HHHHHH.', '.LOOLHH.', '.LMMLHH.',
   '..HHHH..', 'WBBBBBB.', 'BBBBBBB.', 'BB.BBBB.', '.TTT.T..',
   '.TTT.T..', '.EEE.E..', 'EEEE..E.', '........'],
  // walkB
  ['..DDDD..', '.HHHHHH.', '.HHHHHH.', '.LOOLHH.', '.LMMLHH.',
   '..HHHH..', 'WBBBBBB.', 'BBBBBBB.', 'BB.BBBB.', '.T.TTT..',
   '.T.TTT..', '.E.EEE..', 'E...EEEE', '........'],
  // attack
  ['..DDDD..', '.HHHHHH.', '.HHHHHH.', '.LOOLHH.', '.LMMLHH.',
   '..HHHH..', 'WBBBBBBW', 'BBBBBBB.', 'BBBBBBB.', '.TT.TT..',
   '.TT.TT..', '.EE.EE..', '.EE..EE.', '........'],
];

const SPRITE_SET: Record<string, string[][]> = {
  owl: OWL, fox: FOX, cat: CAT, panda: PANDA, brain: BRAIN, sage: SAGE,
};

// ── Agent definitions ──────────────────────────────────────────────────────

interface WeaponDef {
  name: string;
  color: string;
  symbol: string;
  size: number;
  damage: [number, number];
}

interface AgentDef {
  id: string;
  name: string;
  emoji: string;
  sprite: string;
  glowColor: string;
  colors: Record<string, string>;
  weapon: WeaponDef;
  speeches: string[];
  battleSpeeches: string[];
}

const AGENTS: AgentDef[] = [
  {
    id: 'finance', name: 'Owlbert', emoji: '🦉', sprite: 'owl',
    glowColor: '#d4a017',
    colors: {
      H: '#d4a017', D: '#5c3d11', L: '#fef3c7', O: '#1c2333',
      M: '#fbbf24', B: '#92400e', T: '#78350f', E: '#451a03', W: '#ffd700',
    },
    weapon: { name: 'GOLD COIN', color: '#ffd700', symbol: '💰', size: 6, damage: [3, 7] },
    speeches: ['💰 Balancing books!', '📊 Anomaly!', '🦉 All healthy!', '💷 Checking...', '⚠️ Watch spend!'],
    battleSpeeches: ['AUDIT BLAST!', 'BALANCE SHEET!', 'Dividend SLAM!', 'Tax STRIKE!', 'Cash flow SURGE!'],
  },
  {
    id: 'content', name: 'Foxy', emoji: '🦊', sprite: 'fox',
    glowColor: '#e85d04',
    colors: {
      H: '#e85d04', D: '#7c2d12', L: '#fff7ed', O: '#1c2333',
      M: '#9a3412', B: '#a78bfa', T: '#6d28d9', E: '#4c1d95', W: '#c4b5fd',
    },
    weapon: { name: 'PEN WAND', color: '#c4b5fd', symbol: '✍️', size: 4, damage: [2, 6] },
    speeches: ['✍️ Creating!', '🦊 Going viral!', '💡 Hot take!', '📱 LinkedIn!', '🎬 Action!'],
    battleSpeeches: ['VIRAL POST!', 'Content STRIKE!', 'Algorithm BLAST!', 'Engagement SURGE!', 'Click-bait HIT!'],
  },
  {
    id: 'education', name: 'Whiskers', emoji: '🐱', sprite: 'cat',
    glowColor: '#0891b2',
    colors: {
      H: '#94a3b8', D: '#1e293b', L: '#f1f5f9', O: '#1c2333',
      M: '#fca5a5', B: '#0891b2', T: '#164e63', E: '#0c2d3d',
      W: '#60a5fa', G: '#7dd3fc',
    },
    weapon: { name: 'KNOWLEDGE BOOK', color: '#60a5fa', symbol: '📚', size: 7, damage: [2, 5] },
    speeches: ['📚 Learning!', '🐱 New insights!', '🧠 Knowledge!', '🔗 Link saved!', '📖 Processing!'],
    battleSpeeches: ['KNOWLEDGE BOMB!', 'Wikipedia BLITZ!', 'PEER REVIEW!', 'Cited source!', 'Bibliography BLAST!'],
  },
  {
    id: 'health', name: 'Bamboo', emoji: '🐼', sprite: 'panda',
    glowColor: '#16a34a',
    colors: {
      H: '#e2e8f0', D: '#1e293b', L: '#f8fafc', O: '#e2e8f0',
      M: '#1e293b', B: '#16a34a', T: '#14532d', E: '#0a2e1a',
      W: '#4ade80', X: '#1e293b',   // X = panda eye patches
    },
    weapon: { name: 'DUMBBELL', color: '#4ade80', symbol: '💪', size: 8, damage: [4, 8] },
    speeches: ['🏃 Keep moving!', '🐼 Feeling great!', '💚 Streak!', '😴 8h goal!', '💧 Hydrate!'],
    battleSpeeches: ['GAINS SLAM!', 'Protein SHAKE!', 'HIIT COMBO!', 'Macro BLAST!', 'Rest day? NOT!'],
  },
  {
    id: 'braindump', name: 'Brain', emoji: '🧠', sprite: 'brain',
    glowColor: '#c026d3',
    colors: {
      H: '#e879f9', D: '#701a75', L: '#fdf4ff', O: '#1c2333',
      M: '#c026d3', B: '#c026d3', T: '#4c1d95', E: '#2d0d5c', W: '#f0abfc',
    },
    weapon: { name: 'LIGHTNING', color: '#f0abfc', symbol: '⚡', size: 5, damage: [2, 9] },
    speeches: ['🧠 Thought captured!', '💭 Mind dump!', '⚡ Queued!', '💡 Idea!', '🔮 Processing!'],
    battleSpeeches: ['THOUGHT SURGE!', 'Idea EXPLOSION!', 'ADHD SCATTER!', 'FOCUS BEAM!', 'Synapse FIRE!'],
  },
  {
    id: 'research', name: 'Sage', emoji: '🔬', sprite: 'sage',
    glowColor: '#4f46e5',
    colors: {
      H: '#c7d2fe', D: '#1e1b4b', L: '#ede9fe', O: '#1c2333',
      M: '#4f46e5', B: '#e0e7ff', T: '#3730a3', E: '#1e1b4b', W: '#818cf8',
    },
    weapon: { name: 'SCIENCE BEAM', color: '#818cf8', symbol: '🔬', size: 5, damage: [3, 6] },
    speeches: ['🔬 Research mode!', '📡 Scanning!', '🗂 Updated!', '🧩 Pattern found!', '📊 Analysing!'],
    battleSpeeches: ['DATA DUMP!', 'Correlation STRIKE!', 'p<0.05 BLAST!', 'Peer review SHOT!', 'Hypothesis SMASH!'],
  },
];

// ── Runtime types ──────────────────────────────────────────────────────────

type CharState = 'walking' | 'idle' | 'working' | 'battling' | 'fainted' | 'victory';

interface Char {
  agentIdx: number;
  x: number; y: number;
  vx: number; vy: number;
  facing: 1 | -1;
  state: CharState;
  animFrame: number;
  animTick: number;
  dirTick: number;
  speechText: string | null;
  speechTick: number;
  bobOffset: number;
  bobPhase: number;
  agentStatus: string;
  // Battle
  hp: number;
  maxHp: number;
  hitFlash: number;       // ticks of white flash on hit
  faintTick: number;      // countdown to respawn
  faintAngle: number;     // rotation when fainted (0→90°)
  victoryTick: number;    // bounce on win
  // Cursor
  cursorFlee: boolean;
  // Attack flash
  attackFlash: number;
}

interface Battle {
  aIdx: number;
  bIdx: number;
  hpA: number;
  hpB: number;
  attackTimer: number;
  turn: 'A' | 'B';  // whose turn
}

interface Projectile {
  x: number; y: number;
  tx: number; ty: number;
  color: string;
  weaponName: string;
  damage: number;
  targetIdx: number;
  sourceIdx: number;
}

interface FloatText {
  x: number; y: number;
  text: string;
  color: string;
  alpha: number;
  vy: number;
  life: number;
  maxLife: number;
}

// ── Drawing helpers ────────────────────────────────────────────────────────

function drawSprite(
  ctx: CanvasRenderingContext2D,
  rows: string[],
  colors: Record<string, string>,
  x: number, y: number,
  scale: number,
  flipX: boolean,
  alpha = 1,
  whiteFlash = false,
) {
  const numCols = rows[0].length;
  if (alpha < 1) ctx.globalAlpha = alpha;
  for (let r = 0; r < rows.length; r++) {
    for (let c = 0; c < numCols; c++) {
      const ch = rows[r][c];
      if (ch === '.') continue;
      ctx.fillStyle = whiteFlash ? '#ffffff' : (colors[ch] ?? '#ff00ff');
      const dc = flipX ? numCols - 1 - c : c;
      ctx.fillRect(x + dc * scale, y + r * scale, scale, scale);
    }
  }
  if (alpha < 1) ctx.globalAlpha = 1;
}

function drawGlow(ctx: CanvasRenderingContext2D, x: number, y: number, color: string, pulse = 1) {
  ctx.save();
  ctx.globalAlpha = 0.18 * pulse;
  ctx.shadowColor = color;
  ctx.shadowBlur = 20;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.ellipse(x + SW / 2, y + SH / 2, SW / 1.4, SH / 1.6, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawShadow(ctx: CanvasRenderingContext2D, x: number, y: number, color: string) {
  ctx.save();
  ctx.globalAlpha = 0.22;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.ellipse(x + SW / 2, y + SH + 2, SW / 2.4, 4, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawHPBar(ctx: CanvasRenderingContext2D, x: number, y: number, hp: number, maxHp: number) {
  const w = SW;
  const h = 5;
  const by = y - 14;
  const pct = Math.max(0, hp / maxHp);
  const fillColor = pct > 0.6 ? '#22c55e' : pct > 0.3 ? '#f59e0b' : '#ef4444';
  // bg
  ctx.fillStyle = '#0f0c1a';
  ctx.fillRect(x, by, w, h);
  // fill
  ctx.fillStyle = fillColor;
  ctx.fillRect(x, by, Math.round(w * pct), h);
  // border
  ctx.strokeStyle = '#4a3a70';
  ctx.lineWidth = 1;
  ctx.strokeRect(x, by, w, h);
}

function drawSpeechBubble(ctx: CanvasRenderingContext2D, text: string, cx: number, by: number, alpha: number) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.font = 'bold 11px system-ui, sans-serif';
  const pad = 7;
  const tw = ctx.measureText(text).width;
  const bw = tw + pad * 2;
  const bh = 22;
  let bx = cx - bw / 2;
  const W = ctx.canvas.width / (window.devicePixelRatio || 1);
  if (bx < 4) bx = 4;
  if (bx + bw > W - 4) bx = W - 4 - bw;
  const bubbleY = by - bh - 10;
  ctx.fillStyle = '#1a1530';
  ctx.strokeStyle = '#7c3aed';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.roundRect(bx, bubbleY, bw, bh, 6);
  ctx.fill();
  ctx.stroke();
  // tail
  ctx.beginPath();
  ctx.moveTo(cx - 4, bubbleY + bh);
  ctx.lineTo(cx, bubbleY + bh + 7);
  ctx.lineTo(cx + 4, bubbleY + bh);
  ctx.fillStyle = '#1a1530';
  ctx.fill();
  ctx.fillStyle = '#e6e2f4';
  ctx.globalAlpha = alpha;
  ctx.fillText(text, bx + pad, bubbleY + bh - 7);
  ctx.restore();
}

function drawNameLabel(ctx: CanvasRenderingContext2D, name: string, emoji: string, cx: number, by: number) {
  ctx.save();
  ctx.font = '10px system-ui, sans-serif';
  const label = `${emoji} ${name}`;
  const tw = ctx.measureText(label).width;
  ctx.globalAlpha = 0.75;
  ctx.fillStyle = '#0f0c1a';
  ctx.fillRect(cx - tw / 2 - 3, by + 3, tw + 6, 13);
  ctx.globalAlpha = 1;
  ctx.fillStyle = '#c8c0e0';
  ctx.fillText(label, cx - tw / 2, by + 13);
  ctx.restore();
}

function drawProjectile(ctx: CanvasRenderingContext2D, proj: Projectile) {
  ctx.save();
  const { x, y, color, weaponName } = proj;

  switch (weaponName) {
    case 'GOLD COIN':
      ctx.fillStyle = color;
      ctx.shadowColor = color; ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.arc(x, y, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#fef9c3';
      ctx.beginPath();
      ctx.arc(x - 1, y - 1, 2, 0, Math.PI * 2);
      ctx.fill();
      break;

    case 'PEN WAND': {
      const dx = proj.tx - proj.x; const dy = proj.ty - proj.y;
      const angle = Math.atan2(dy, dx);
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.shadowColor = color; ctx.shadowBlur = 10;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(x - Math.cos(angle) * 8, y - Math.sin(angle) * 8);
      ctx.lineTo(x + Math.cos(angle) * 8, y + Math.sin(angle) * 8);
      ctx.stroke();
      break;
    }

    case 'KNOWLEDGE BOOK':
      ctx.fillStyle = color;
      ctx.shadowColor = color; ctx.shadowBlur = 6;
      ctx.fillRect(x - 7, y - 5, 14, 10);
      ctx.fillStyle = '#1e3a5f';
      ctx.fillRect(x - 1, y - 5, 2, 10);
      break;

    case 'DUMBBELL':
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.shadowColor = color; ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.moveTo(x - 9, y); ctx.lineTo(x + 9, y);
      ctx.stroke();
      ctx.fillStyle = color;
      [x - 9, x + 9].forEach(px => {
        ctx.beginPath();
        ctx.arc(px, y, 5, 0, Math.PI * 2);
        ctx.fill();
      });
      break;

    case 'LIGHTNING': {
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.shadowColor = color; ctx.shadowBlur = 14;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(x - 4, y - 8);
      ctx.lineTo(x + 2, y - 1);
      ctx.lineTo(x - 2, y + 1);
      ctx.lineTo(x + 4, y + 8);
      ctx.stroke();
      break;
    }

    case 'SCIENCE BEAM': {
      ctx.fillStyle = color;
      ctx.shadowColor = color; ctx.shadowBlur = 16;
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 0.35;
      ctx.beginPath();
      ctx.arc(x, y, 10, 0, Math.PI * 2);
      ctx.fill();
      break;
    }

    default:
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, Math.PI * 2);
      ctx.fill();
  }

  ctx.restore();
}

function drawFloatText(ctx: CanvasRenderingContext2D, ft: FloatText) {
  ctx.save();
  ctx.globalAlpha = ft.alpha;
  ctx.font = `bold ${ft.text.startsWith('-') || ft.text.startsWith('+') ? 14 : 11}px system-ui, sans-serif`;
  ctx.fillStyle = ft.color;
  ctx.shadowColor = ft.color;
  ctx.shadowBlur = 6;
  ctx.textAlign = 'center';
  ctx.fillText(ft.text, ft.x, ft.y);
  ctx.restore();
}

// ── Cursor burst ───────────────────────────────────────────────────────────

interface Burst { x: number; y: number; r: number; maxR: number; alpha: number; color: string; }

// ── Main component ─────────────────────────────────────────────────────────

interface PixelAgentsCanvasProps {
  wanderZone?: number;
}

export function PixelAgentsCanvas({ wanderZone = 0.62 }: PixelAgentsCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const charsRef = useRef<Char[]>([]);
  const battlesRef = useRef<Battle[]>([]);
  const projectilesRef = useRef<Projectile[]>([]);
  const floatTextsRef = useRef<FloatText[]>([]);
  const burstsRef = useRef<Burst[]>([]);
  const rafRef = useRef<number>(0);
  const tickRef = useRef(0);
  const cursorRef = useRef({ x: -999, y: -999 });

  const [visible, setVisible] = useState(() => {
    try { return localStorage.getItem('vaf_pixel_agents') !== 'hidden'; } catch { return true; }
  });
  const [statusMap, setStatusMap] = useState<Record<string, string>>({});

  // ── Init ────────────────────────────────────────────────────────────────
  const initChars = useCallback((W: number, H: number) => {
    const yMin = H * (1 - wanderZone);
    charsRef.current = AGENTS.map((_, idx) => ({
      agentIdx: idx,
      x: 60 + Math.random() * (W - SW - 120),
      y: yMin + Math.random() * (H - yMin - SH - 30),
      vx: (Math.random() - 0.5) * WALK_SPEED * 2,
      vy: (Math.random() - 0.5) * WALK_SPEED * 0.4,
      facing: Math.random() > 0.5 ? 1 : -1,
      state: 'walking',
      animFrame: 1,
      animTick: ANIM_WALK_RATE,
      dirTick: DIR_CHANGE_MIN + Math.random() * (DIR_CHANGE_MAX - DIR_CHANGE_MIN),
      speechText: null,
      speechTick: 0,
      bobOffset: 0,
      bobPhase: Math.random() * Math.PI * 2,
      agentStatus: 'idle',
      hp: BATTLE_HP,
      maxHp: BATTLE_HP,
      hitFlash: 0,
      faintTick: 0,
      faintAngle: 0,
      victoryTick: 0,
      cursorFlee: false,
      attackFlash: 0,
    }));
  }, [wanderZone]);

  // ── Status poll ─────────────────────────────────────────────────────────
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) return;
      const data = await res.json();
      const map: Record<string, string> = {};
      const src = data?.agents ?? data;
      for (const [id, val] of Object.entries(src as Record<string, any>)) {
        map[id] = typeof val === 'string' ? val : (val as any)?.status ?? 'idle';
      }
      setStatusMap(map);
    } catch { /* offline */ }
  }, []);

  // ── Helpers ─────────────────────────────────────────────────────────────
  function addFloat(x: number, y: number, text: string, color: string, life = 60) {
    floatTextsRef.current.push({ x, y, text, color, alpha: 1, vy: -1.2, life, maxLife: life });
  }

  function randDamage(w: WeaponDef): number {
    return Math.floor(Math.random() * (w.damage[1] - w.damage[0] + 1)) + w.damage[0];
  }

  function isInBattle(idx: number): boolean {
    return battlesRef.current.some(b => b.aIdx === idx || b.bIdx === idx);
  }

  function getActiveBattle(idx: number): Battle | null {
    return battlesRef.current.find(b => b.aIdx === idx || b.bIdx === idx) ?? null;
  }

  // ── Game loop ────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!visible) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const resize = () => {
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      const ctx = canvas.getContext('2d');
      if (ctx) ctx.scale(dpr, dpr);
      if (charsRef.current.length === 0) initChars(window.innerWidth, window.innerHeight);
    };
    resize();
    window.addEventListener('resize', resize);

    // Track cursor via document — canvas has pointerEvents:none so we must use document
    const onMouseMove = (e: MouseEvent) => { cursorRef.current = { x: e.clientX, y: e.clientY }; };
    document.addEventListener('mousemove', onMouseMove);

    // Click to interact — only fire effect when clicking directly on an agent sprite
    const onClick = (e: MouseEvent) => {
      // Only handle if clicking on/near an agent — don't steal clicks from UI elements
      const { x: cx, y: cy } = { x: e.clientX, y: e.clientY };
      const hitAgent = charsRef.current.some(ch =>
        ch.state !== 'fainted' &&
        cx >= ch.x - 4 && cx <= ch.x + SW + 4 &&
        cy >= ch.y - 4 && cy <= ch.y + SH + 4
      );
      if (!hitAgent) return; // let click pass through to UI
      e.stopPropagation();
      // Burst effect
      const agent = AGENTS[Math.floor(Math.random() * AGENTS.length)];
      burstsRef.current.push({ x: cx, y: cy, r: 0, maxR: 40, alpha: 0.8, color: agent.glowColor });

      // Find character under click
      for (const ch of charsRef.current) {
        if (ch.state === 'fainted') continue;
        if (cx >= ch.x && cx <= ch.x + SW && cy >= ch.y && cy <= ch.y + SH) {
          const a = AGENTS[ch.agentIdx];
          // Launch projectile toward click position
          projectilesRef.current.push({
            x: ch.x + SW / 2, y: ch.y + SH / 2,
            tx: cx, ty: cy,
            color: a.weapon.color,
            weaponName: a.weapon.name,
            damage: 0,
            targetIdx: -1, // -1 = toward cursor, no target char
            sourceIdx: ch.agentIdx,
          });
          const speech = a.battleSpeeches[Math.floor(Math.random() * a.battleSpeeches.length)];
          ch.speechText = `${a.emoji} ${speech}`;
          ch.speechTick = SPEECH_DURATION;
          ch.animFrame = 3; ch.animTick = 20;
          break;
        }
      }
    };
    document.addEventListener('click', onClick);

    fetchStatus();
    const statusInterval = setInterval(fetchStatus, 15000);

    const draw = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const W = window.innerWidth;
      const H = window.innerHeight;
      const yMin = H * (1 - wanderZone);

      ctx.clearRect(0, 0, W, H);
      tickRef.current++;
      const tick = tickRef.current;
      const chars = charsRef.current;
      const cursor = cursorRef.current;

      // ── 1. Update bursts ────────────────────────────────────────────────
      burstsRef.current = burstsRef.current.filter(b => b.alpha > 0);
      for (const b of burstsRef.current) {
        b.r += 2; b.alpha -= 0.05;
        ctx.save();
        ctx.globalAlpha = b.alpha;
        ctx.strokeStyle = b.color;
        ctx.lineWidth = 2;
        ctx.shadowColor = b.color;
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      }

      // ── 2. Update & draw float texts ────────────────────────────────────
      floatTextsRef.current = floatTextsRef.current.filter(ft => ft.life > 0);
      for (const ft of floatTextsRef.current) {
        ft.y += ft.vy;
        ft.life--;
        ft.alpha = ft.life / ft.maxLife;
        drawFloatText(ctx, ft);
      }

      // ── 3. Update projectiles ────────────────────────────────────────────
      projectilesRef.current = projectilesRef.current.filter(p => {
        const dx = p.tx - p.x;
        const dy = p.ty - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < PROJ_SPEED + 2) {
          // Hit!
          if (p.targetIdx >= 0 && p.damage > 0) {
            const tch = chars[p.targetIdx];
            if (tch && tch.state !== 'fainted') {
              tch.hitFlash = HIT_FLASH_DURATION;
              // Find the battle and apply damage
              const battle = battlesRef.current.find(b =>
                (b.aIdx === p.sourceIdx && b.bIdx === p.targetIdx) ||
                (b.bIdx === p.sourceIdx && b.aIdx === p.targetIdx)
              );
              if (battle) {
                if (battle.bIdx === p.targetIdx) {
                  battle.hpB = Math.max(0, battle.hpB - p.damage);
                  tch.hp = battle.hpB;
                } else {
                  battle.hpA = Math.max(0, battle.hpA - p.damage);
                  tch.hp = battle.hpA;
                }
                addFloat(tch.x + SW / 2, tch.y - 10, `-${p.damage}`, '#ef4444', 55);

                // Check KO
                const hpRemaining = battle.bIdx === p.targetIdx ? battle.hpB : battle.hpA;
                if (hpRemaining <= 0) {
                  // Faint target
                  tch.state = 'fainted';
                  tch.faintTick = FAINT_DURATION;
                  tch.faintAngle = 0;
                  addFloat(tch.x + SW / 2, tch.y - 20, '💫 FAINTED!', '#fbbf24', 90);
                  // Victory for source
                  const winner = chars[p.sourceIdx];
                  if (winner) {
                    winner.state = 'victory';
                    winner.victoryTick = 80;
                    const wa = AGENTS[winner.agentIdx];
                    winner.speechText = `${wa.emoji} Gotcha! ⭐`;
                    winner.speechTick = SPEECH_DURATION;
                    addFloat(winner.x + SW / 2, winner.y - 20, `⭐ WIN!`, wa.glowColor, 70);
                  }
                  // Remove battle
                  battlesRef.current = battlesRef.current.filter(b => b !== battle);
                }
              }
            }
          }
          return false; // remove projectile
        }
        p.x += (dx / dist) * PROJ_SPEED;
        p.y += (dy / dist) * PROJ_SPEED;
        drawProjectile(ctx, p);
        return true;
      });

      // ── 4. Battle management — check for new battles ────────────────────
      for (let i = 0; i < chars.length; i++) {
        for (let j = i + 1; j < chars.length; j++) {
          const ca = chars[i], cb = chars[j];
          if (ca.state === 'fainted' || cb.state === 'fainted') continue;
          if (isInBattle(i) || isInBattle(j)) continue;
          const dx = ca.x - cb.x, dy = ca.y - cb.y;
          if (Math.sqrt(dx * dx + dy * dy) < BATTLE_RANGE) {
            battlesRef.current.push({
              aIdx: i, bIdx: j,
              hpA: BATTLE_HP, hpB: BATTLE_HP,
              attackTimer: ATTACK_INTERVAL,
              turn: 'A',
            });
            ca.state = 'battling'; cb.state = 'battling';
            ca.hp = BATTLE_HP; cb.hp = BATTLE_HP;
            const aa = AGENTS[ca.agentIdx], ab = AGENTS[cb.agentIdx];
            ca.speechText = `${aa.emoji} Battle time!`;
            cb.speechText = `${ab.emoji} Fight!`;
            ca.speechTick = 60; cb.speechTick = 60;
          }
        }
      }

      // ── 5. Process active battles ────────────────────────────────────────
      for (const battle of battlesRef.current) {
        const ca = chars[battle.aIdx], cb = chars[battle.bIdx];
        if (!ca || !cb) continue;

        // Face each other
        ca.facing = ca.x < cb.x ? 1 : -1;
        cb.facing = cb.x < ca.x ? 1 : -1;

        // Maintain slight separation
        const dx = ca.x - cb.x, dy = ca.y - cb.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const targetDist = SW + 10;
        if (dist < targetDist && dist > 0) {
          const push = (targetDist - dist) / targetDist * 0.5;
          ca.x += (dx / dist) * push;
          cb.x -= (dx / dist) * push;
        }

        battle.attackTimer--;
        if (battle.attackTimer <= 0) {
          battle.attackTimer = ATTACK_INTERVAL;
          const attacker = battle.turn === 'A' ? ca : cb;
          const defender = battle.turn === 'A' ? cb : ca;
          const attackerAgent = AGENTS[attacker.agentIdx];

          attacker.animFrame = 3; attacker.animTick = 18;
          attacker.attackFlash = 12;
          const dmg = randDamage(attackerAgent.weapon);
          const speech = attackerAgent.battleSpeeches[Math.floor(Math.random() * attackerAgent.battleSpeeches.length)];
          attacker.speechText = `${attackerAgent.emoji} ${speech}`;
          attacker.speechTick = 80;

          projectilesRef.current.push({
            x: attacker.x + SW / 2,
            y: attacker.y + SH / 3,
            tx: defender.x + SW / 2,
            ty: defender.y + SH / 3,
            color: attackerAgent.weapon.color,
            weaponName: attackerAgent.weapon.name,
            damage: dmg,
            targetIdx: battle.turn === 'A' ? battle.bIdx : battle.aIdx,
            sourceIdx: battle.turn === 'A' ? battle.aIdx : battle.bIdx,
          });

          battle.turn = battle.turn === 'A' ? 'B' : 'A';
        }
      }

      // ── 6. Update each character ─────────────────────────────────────────
      for (const ch of chars) {
        const agent = AGENTS[ch.agentIdx];
        const st = statusMap[agent.id] ?? 'idle';
        ch.agentStatus = st;

        // Fainted state
        if (ch.state === 'fainted') {
          ch.faintTick--;
          ch.faintAngle = Math.min(Math.PI / 2, ch.faintAngle + 0.08);
          if (ch.faintTick <= 0) {
            ch.state = 'walking';
            ch.hp = BATTLE_HP;
            ch.faintAngle = 0;
            ch.speechText = `${agent.emoji} I'm back!`;
            ch.speechTick = SPEECH_DURATION;
          }
          // Draw fainted (rotated)
          ctx.save();
          const cx = ch.x + SW / 2, cy = ch.y + SH / 2;
          ctx.translate(cx, cy);
          ctx.rotate(ch.faintAngle);
          ctx.translate(-SW / 2, -SH / 2);
          const alpha = ch.faintTick > 60 ? 1 : ch.faintTick / 60;
          drawSprite(ctx, SPRITE_SET[agent.sprite][0], agent.colors, 0, 0, SCALE, ch.facing === -1, alpha);
          ctx.restore();
          drawNameLabel(ctx, agent.name, agent.emoji, ch.x + SW / 2, ch.y + SH);
          continue;
        }

        // Victory bounce
        if (ch.state === 'victory') {
          ch.victoryTick--;
          ch.bobPhase += 0.25;
          ch.bobOffset = Math.abs(Math.sin(ch.bobPhase)) * -12;
          if (ch.victoryTick <= 0) {
            ch.state = 'walking';
            ch.bobOffset = 0;
          }
        }

        // Battling chars — just stand and face enemy
        if (ch.state === 'battling') {
          ch.animFrame = isInBattle(ch.agentIdx) ? 0 : 1;
          ch.bobPhase += 0.03;
          ch.bobOffset = Math.sin(ch.bobPhase) * 1.5;
        }

        // Cursor flee / awareness
        const cdx = ch.x + SW / 2 - cursor.x;
        const cdy = ch.y + SH / 2 - cursor.y;
        const cursorDist = Math.sqrt(cdx * cdx + cdy * cdy);
        ch.cursorFlee = false;

        if ((ch.state as CharState) !== 'battling' && (ch.state as CharState) !== 'fainted' && (ch.state as CharState) !== 'victory') {
          if (cursorDist < CURSOR_FLEE_RANGE) {
            // Flee!
            ch.cursorFlee = true;
            const mag = cursorDist || 1;
            ch.vx = (cdx / mag) * WALK_SPEED_FLEE;
            ch.vy = (cdy / mag) * WALK_SPEED_FLEE * 0.3;
            ch.facing = ch.vx >= 0 ? 1 : -1;
            ch.state = 'walking';
            if (Math.random() < 0.01) {
              ch.speechText = '😱 Cursor!';
              ch.speechTick = 40;
            }
          } else if (cursorDist < CURSOR_AWARE_RANGE) {
            // Look toward cursor
            ch.facing = cursor.x > ch.x + SW / 2 ? 1 : -1;
          }
        }

        // Normal movement
        if (ch.state === 'walking' && !ch.cursorFlee) {
          const speed = st === 'warning' ? WALK_SPEED_ANXIOUS : WALK_SPEED;
          ch.dirTick--;
          if (ch.dirTick <= 0) {
            const angle = Math.random() * Math.PI * 2;
            ch.vx = Math.cos(angle) * speed;
            ch.vy = Math.sin(angle) * speed * 0.3;
            ch.facing = ch.vx >= 0 ? 1 : -1;
            ch.dirTick = DIR_CHANGE_MIN + Math.random() * (DIR_CHANGE_MAX - DIR_CHANGE_MIN);
          }
        }

        if ((ch.state === 'walking') || ch.cursorFlee) {
          ch.x += ch.vx;
          ch.y += ch.vy;
          if (ch.x < 0) { ch.x = 0; ch.vx = Math.abs(ch.vx); ch.facing = 1; }
          if (ch.x > W - SW) { ch.x = W - SW; ch.vx = -Math.abs(ch.vx); ch.facing = -1; }
          if (ch.y < yMin) { ch.y = yMin; ch.vy = Math.abs(ch.vy); }
          if (ch.y > H - SH - 24) { ch.y = H - SH - 24; ch.vy = -Math.abs(ch.vy); }
        }

        // Idle
        if (ch.state === 'idle') {
          ch.bobPhase += 0.04;
          ch.bobOffset = Math.sin(ch.bobPhase) * 2.5;
        }

        // Separation — two-tier: soft steering at range, hard push when overlapping
        if (ch.state !== 'battling') {
          for (const other of chars) {
            if (other === ch || other.state === 'fainted') continue;
            const dx = ch.x - other.x, dy = ch.y - other.y;
            const d = Math.sqrt(dx * dx + dy * dy);
            const softZone = SW * 2.2;   // 70px — start steering early
            const hardZone = SW + 8;     // 40px — hard separation

            if (d < softZone && d > 0) {
              const nx = dx / d, ny = dy / d;
              if (d < hardZone) {
                // Hard push: direct position correction + velocity deflection
                const pushStrength = (hardZone - d) / hardZone * 1.8;
                ch.x += nx * pushStrength;
                ch.y += ny * pushStrength * 0.4;
                // Bounce velocity away from the other agent
                const dot = ch.vx * nx + ch.vy * ny;
                if (dot < 0) {
                  ch.vx -= dot * nx * 1.5;
                  ch.vy -= dot * ny * 1.5;
                }
              } else {
                // Soft steer: smoothly deflect velocity to avoid approaching
                const approach = ch.vx * (-nx) + ch.vy * (-ny); // how much heading toward other
                if (approach > 0) {
                  const steer = approach * (1 - d / softZone) * 0.18;
                  ch.vx += nx * steer;
                  ch.vy += ny * steer * 0.4;
                  // Re-normalise speed
                  const spd = Math.sqrt(ch.vx * ch.vx + ch.vy * ch.vy);
                  const targetSpd = st === 'warning' ? WALK_SPEED_ANXIOUS : WALK_SPEED;
                  if (spd > targetSpd * 1.5) {
                    ch.vx = (ch.vx / spd) * targetSpd;
                    ch.vy = (ch.vy / spd) * targetSpd;
                  }
                }
              }
            }
          }
        }

        // Animate walk frames
        if (ch.state === 'walking' || ch.cursorFlee) {
          ch.animTick--;
          if (ch.animTick <= 0) {
            ch.animFrame = ch.animFrame === 1 ? 2 : 1;
            ch.animTick = ANIM_WALK_RATE;
          }
        } else if (ch.state !== 'battling') {
          ch.animFrame = 0;
        }

        // Decay attack flash
        if (ch.attackFlash > 0) ch.attackFlash--;

        // Speech
        if (ch.speechTick > 0) {
          ch.speechTick--;
        } else if (ch.state !== 'battling' && Math.random() < SPEECH_CHANCE) {
          ch.speechText = agent.speeches[Math.floor(Math.random() * agent.speeches.length)];
          ch.speechTick = SPEECH_DURATION;
        } else if (ch.speechTick === 0) {
          ch.speechText = null;
        }

        // ── Draw ──────────────────────────────────────────────────────────
        const drawX = Math.round(ch.x);
        const drawY = Math.round(ch.y + ch.bobOffset);
        const flipX = ch.facing === -1;
        const glowing = ch.state === 'battling' || ch.attackFlash > 0;
        const pulse = ch.state === 'battling'
          ? 0.5 + 0.5 * Math.sin(tick / 15)
          : ch.state === 'victory'
            ? 0.6 + 0.6 * Math.abs(Math.sin(tick / 8))
            : 1;

        drawGlow(ctx, drawX, drawY, agent.glowColor, glowing ? pulse * 1.5 : 1);
        drawShadow(ctx, drawX, drawY, agent.glowColor);

        const frames = SPRITE_SET[agent.sprite];
        const frame = frames[Math.min(ch.animFrame, frames.length - 1)];
        drawSprite(ctx, frame, agent.colors, drawX, drawY, SCALE, flipX, 1, ch.hitFlash > 0);
        if (ch.hitFlash > 0) ch.hitFlash--;

        // HP bar in battle
        if (ch.state === 'battling') {
          drawHPBar(ctx, drawX, drawY, ch.hp, ch.maxHp);
        }

        drawNameLabel(ctx, agent.name, agent.emoji, drawX + SW / 2, drawY + SH);

        // Speech bubble
        if (ch.speechText && ch.speechTick > 0) {
          const fade = Math.min(1, ch.speechTick / 20, (SPEECH_DURATION - ch.speechTick) / 15 + 0.1);
          drawSpeechBubble(ctx, ch.speechText, drawX + SW / 2, drawY, fade);
        }

        // Cursor proximity glow
        if (cursorDist < CURSOR_AWARE_RANGE && (ch.state as CharState) !== 'fainted') {
          ctx.save();
          ctx.globalAlpha = (1 - cursorDist / CURSOR_AWARE_RANGE) * 0.12;
          ctx.fillStyle = agent.glowColor;
          ctx.beginPath();
          ctx.ellipse(drawX + SW / 2, drawY + SH / 2, SW, SH / 1.5, 0, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }
      }

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(rafRef.current);
      clearInterval(statusInterval);
      window.removeEventListener('resize', resize);
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('click', onClick);
    };
  }, [visible, wanderZone, fetchStatus, statusMap, initChars]);

  // Status changes trigger speech
  useEffect(() => {
    for (const ch of charsRef.current) {
      const agent = AGENTS[ch.agentIdx];
      const st = statusMap[agent.id] ?? 'idle';
      if (st !== ch.agentStatus && ch.state !== 'fainted') {
        ch.speechText = agent.speeches[Math.floor(Math.random() * agent.speeches.length)];
        ch.speechTick = SPEECH_DURATION;
      }
    }
  }, [statusMap]);

  const toggle = () => {
    setVisible(v => {
      const next = !v;
      try { localStorage.setItem('vaf_pixel_agents', next ? 'visible' : 'hidden'); } catch {}
      // Reset battles/projectiles when toggled
      if (!next) {
        battlesRef.current = [];
        projectilesRef.current = [];
        floatTextsRef.current = [];
      }
      return next;
    });
  };

  return (
    <>
      {visible && (
        <canvas
          ref={canvasRef}
          style={{
            position: 'fixed', top: 0, left: 0,
            pointerEvents: 'none',  // pass all clicks through to UI — agents tracked via document events
            zIndex: 999,
          }}
        />
      )}

      <button
        onClick={toggle}
        title={visible ? 'Hide agents' : 'Show wandering agents'}
        style={{
          position: 'fixed', bottom: 20, right: 20, zIndex: 1000,
          background: visible ? '#2b1e3e' : '#1a1530',
          border: `1px solid ${visible ? '#a490c2' : '#312b52'}`,
          borderRadius: 20, padding: '6px 14px', cursor: 'pointer',
          color: visible ? '#e6e2f4' : '#7b708f',
          fontSize: 13, fontFamily: 'system-ui, sans-serif', fontWeight: 600,
          display: 'flex', alignItems: 'center', gap: 6,
          boxShadow: visible ? '0 0 12px rgba(164,144,194,0.3)' : 'none',
          transition: 'all 0.2s',
        }}
      >
        <span style={{ fontSize: 15 }}>⚔️</span>
        {visible ? 'Agents ON' : 'Agents OFF'}
      </button>
    </>
  );
}

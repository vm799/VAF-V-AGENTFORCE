import React, { useCallback, useEffect, useRef, useState } from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';

/* ── Types ──────────────────────────────────────────────────────────── */

interface GraphNode {
  id: string;
  label: string;
  type: string;
  category: string;
  colour: string;
  glow: string;
  size: number;
  importance: number;
  description?: string;
  connections?: number;
  // Simulation state
  x: number;
  y: number;
  vx: number;
  vy: number;
  // Interaction state
  pinned: boolean;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  weight: number;
}

interface KnowledgeGraphProps {
  data: any;
}

interface Camera {
  x: number;
  y: number;
  zoom: number;
}

/* ── Constants ──────────────────────────────────────────────────────── */

const MIN_ZOOM = 0.3;
const MAX_ZOOM = 4.0;
const SIM_ITERATIONS = 400;
const REPULSION = 1400;
const ATTRACTION = 0.004;
const CENTER_FORCE = 0.008;
const DAMPING = 0.88;
const AGENT_NODE_RADIUS_FACTOR = 1.0;
const SATELLITE_RADIUS_FACTOR = 0.55;

const NODE_TYPE_META: Record<string, { label: string; shape: 'circle' | 'diamond' | 'hex' }> = {
  agent:        { label: 'Agents',        shape: 'circle'  },
  topic:        { label: 'Topics',        shape: 'circle'  },
  entity:       { label: 'Entities',      shape: 'diamond' },
  metric:       { label: 'Metrics',       shape: 'hex'     },
  anomaly:      { label: 'Anomalies',     shape: 'diamond' },
  idea:         { label: 'Ideas',         shape: 'circle'  },
  draft:        { label: 'Drafts',        shape: 'diamond' },
  score:        { label: 'Scores',        shape: 'hex'     },
  research_job: { label: 'Research Jobs', shape: 'circle'  },
};

/* ── Hex colour helpers ─────────────────────────────────────────────── */

function hexToRgb(hex: string): [number, number, number] {
  const c = hex.replace('#', '');
  return [parseInt(c.slice(0, 2), 16), parseInt(c.slice(2, 4), 16), parseInt(c.slice(4, 6), 16)];
}

function rgbaStr(hex: string, alpha: number): string {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r},${g},${b},${alpha})`;
}

/* ── Component ──────────────────────────────────────────────────────── */

export function KnowledgeGraph({ data }: KnowledgeGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);

  // Refs for simulation state (avoid re-renders during animation)
  const nodesRef = useRef<GraphNode[]>([]);
  const edgesRef = useRef<GraphEdge[]>([]);
  const cameraRef = useRef<Camera>({ x: 0, y: 0, zoom: 1 });
  const dragRef = useRef<{ node: GraphNode | null; offsetX: number; offsetY: number; isPan: boolean }>({
    node: null, offsetX: 0, offsetY: 0, isPan: false,
  });
  const animFrameRef = useRef<number>(0);
  const tickRef = useRef(0);
  const selectedIdRef = useRef<string | null>(null);
  const hoveredIdRef = useRef<string | null>(null);
  const searchRef = useRef('');
  const filtersRef = useRef<Set<string>>(new Set());

  // Keep refs in sync with state
  useEffect(() => { selectedIdRef.current = selectedNode?.id ?? null; }, [selectedNode]);
  useEffect(() => { hoveredIdRef.current = hoveredNode?.id ?? null; }, [hoveredNode]);
  useEffect(() => { searchRef.current = searchQuery.toLowerCase(); }, [searchQuery]);
  useEffect(() => { filtersRef.current = activeFilters; }, [activeFilters]);

  /* ── Initialise simulation ──────────────────────────────────────── */

  useEffect(() => {
    if (!data?.nodes?.length || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d')!;

    // Size canvas to container with retina support
    const resize = () => {
      const rect = canvas.parentElement!.getBoundingClientRect();
      const w = rect.width;
      const h = 520;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      canvas.width = w * 2;
      canvas.height = h * 2;
      ctx.scale(2, 2);
    };
    resize();

    const width = () => canvas.width / 2;
    const height = () => canvas.height / 2;

    // Build node objects
    const nodes: GraphNode[] = data.nodes.map((n: any) => ({
      ...n,
      x: width() / 2 + (Math.random() - 0.5) * width() * 0.5,
      y: height() / 2 + (Math.random() - 0.5) * height() * 0.5,
      vx: 0,
      vy: 0,
      pinned: false,
    }));
    const edges: GraphEdge[] = (data.edges ?? []).map((e: any, i: number) => ({
      ...e,
      id: e.id || `e${i}`,
    }));
    const nodeMap = new Map(nodes.map(n => [n.id, n]));

    nodesRef.current = nodes;
    edgesRef.current = edges;

    // Reset camera to center
    cameraRef.current = { x: 0, y: 0, zoom: 1 };
    tickRef.current = 0;

    /* ── Physics tick ─────────────────────────────────────────────── */

    function simulate() {
      const tick = tickRef.current++;
      if (tick > SIM_ITERATIONS) return; // Simulation settled

      const alpha = Math.max(0, 1 - tick / SIM_ITERATIONS);
      const rep = REPULSION * alpha;
      const att = ATTRACTION * alpha;
      const cen = CENTER_FORCE * alpha;
      const w = width();
      const h = height();

      // Repulsion (Barnes-Hut would be overkill for <100 nodes)
      for (let i = 0; i < nodes.length; i++) {
        if (nodes[i].pinned) continue;
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.1);
          const force = rep / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          if (!nodes[i].pinned) { nodes[i].vx -= fx; nodes[i].vy -= fy; }
          if (!nodes[j].pinned) { nodes[j].vx += fx; nodes[j].vy += fy; }
        }
      }

      // Edge attraction
      for (const edge of edges) {
        const s = nodeMap.get(edge.source);
        const t = nodeMap.get(edge.target);
        if (!s || !t) continue;
        const dx = t.x - s.x;
        const dy = t.y - s.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const idealLen = (s.type === 'agent' || t.type === 'agent') ? 100 : 70;
        const force = (dist - idealLen) * att;
        if (!s.pinned) { s.vx += dx * force; s.vy += dy * force; }
        if (!t.pinned) { t.vx -= dx * force; t.vy -= dy * force; }
      }

      // Center gravity (stronger for agents)
      for (const node of nodes) {
        if (node.pinned) continue;
        const strength = node.type === 'agent' ? cen * 2 : cen;
        node.vx += (w / 2 - node.x) * strength;
        node.vy += (h / 2 - node.y) * strength;
      }

      // Apply velocity
      for (const node of nodes) {
        if (node.pinned) continue;
        node.vx *= DAMPING;
        node.vy *= DAMPING;
        node.x += node.vx;
        node.y += node.vy;
      }
    }

    /* ── Rendering ────────────────────────────────────────────────── */

    function getRadius(node: GraphNode): number {
      const factor = node.type === 'agent' ? AGENT_NODE_RADIUS_FACTOR : SATELLITE_RADIUS_FACTOR;
      return Math.max(node.size * factor, 5);
    }

    function isNodeVisible(node: GraphNode): boolean {
      const filters = filtersRef.current;
      if (filters.size > 0 && !filters.has(node.type)) return false;
      return true;
    }

    function isNodeHighlighted(node: GraphNode): boolean {
      const q = searchRef.current;
      if (!q) return false;
      return node.label.toLowerCase().includes(q) ||
             node.type.toLowerCase().includes(q) ||
             (node.description ?? '').toLowerCase().includes(q);
    }

    function isNodeConnectedToSelected(node: GraphNode): boolean {
      const sel = selectedIdRef.current;
      if (!sel) return false;
      for (const e of edges) {
        if ((e.source === sel && e.target === node.id) ||
            (e.target === sel && e.source === node.id)) return true;
      }
      return false;
    }

    function draw() {
      const c = ctx;
      const w = width();
      const h = height();
      const cam = cameraRef.current;
      const selId = selectedIdRef.current;
      const hovId = hoveredIdRef.current;
      const hasSearch = searchRef.current.length > 0;

      c.clearRect(0, 0, w, h);

      // Background gradient (subtle radial)
      const grad = c.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w * 0.6);
      grad.addColorStop(0, '#131826');
      grad.addColorStop(1, colors.bg.primary);
      c.fillStyle = grad;
      c.fillRect(0, 0, w, h);

      c.save();
      // Apply camera transform
      c.translate(w / 2, h / 2);
      c.scale(cam.zoom, cam.zoom);
      c.translate(-w / 2 + cam.x, -h / 2 + cam.y);

      // ── Draw edges ─────────────────────────────────────────────
      for (const edge of edges) {
        const src = nodeMap.get(edge.source);
        const tgt = nodeMap.get(edge.target);
        if (!src || !tgt) continue;
        if (!isNodeVisible(src) || !isNodeVisible(tgt)) continue;

        const isActive = selId && (edge.source === selId || edge.target === selId);
        const isSearchHit = hasSearch && (isNodeHighlighted(src) || isNodeHighlighted(tgt));
        const dimmed = (selId && !isActive) || (hasSearch && !isSearchHit);

        const alpha = dimmed ? 0.06 : (isActive ? 0.6 : 0.15 + edge.weight * 0.15);
        const lineWidth = isActive ? 1.5 + edge.weight : 0.5 + edge.weight * 0.5;

        c.beginPath();
        c.moveTo(src.x, src.y);
        c.lineTo(tgt.x, tgt.y);
        c.strokeStyle = rgbaStr(src.colour, alpha);
        c.lineWidth = lineWidth;
        c.stroke();

        // Animated particles on active edges
        if (isActive && tickRef.current < SIM_ITERATIONS + 600) {
          const t = ((Date.now() % 3000) / 3000);
          const px = src.x + (tgt.x - src.x) * t;
          const py = src.y + (tgt.y - src.y) * t;
          c.beginPath();
          c.arc(px, py, 2, 0, Math.PI * 2);
          c.fillStyle = rgbaStr(src.colour, 0.8);
          c.fill();
        }

        // Edge label (only on hover/select)
        if (isActive && edge.relation) {
          const mx = (src.x + tgt.x) / 2;
          const my = (src.y + tgt.y) / 2;
          c.font = `9px ${typography.fontFamily}`;
          c.fillStyle = rgbaStr(src.colour, 0.6);
          c.textAlign = 'center';
          c.fillText(edge.relation, mx, my - 4);
        }
      }

      // ── Draw nodes ─────────────────────────────────────────────
      // Sort: agents last (on top)
      const sortedNodes = [...nodes].sort((a, b) => {
        if (a.type === 'agent' && b.type !== 'agent') return 1;
        if (a.type !== 'agent' && b.type === 'agent') return -1;
        return 0;
      });

      for (const node of sortedNodes) {
        if (!isNodeVisible(node)) continue;

        const r = getRadius(node);
        const isSelected = node.id === selId;
        const isHovered = node.id === hovId;
        const isConnected = isNodeConnectedToSelected(node);
        const isSearchHit = hasSearch && isNodeHighlighted(node);
        const dimmed = (selId && !isSelected && !isConnected) || (hasSearch && !isSearchHit);
        const emphasis = isSelected || isHovered;

        // Outer glow
        if (emphasis || node.type === 'agent') {
          const glowR = r * (emphasis ? 3.5 : 2.2);
          const glowGrad = c.createRadialGradient(node.x, node.y, r * 0.5, node.x, node.y, glowR);
          const glowAlpha = emphasis ? 0.35 : (dimmed ? 0.03 : 0.12);
          glowGrad.addColorStop(0, rgbaStr(node.colour, glowAlpha));
          glowGrad.addColorStop(1, rgbaStr(node.colour, 0));
          c.beginPath();
          c.arc(node.x, node.y, glowR, 0, Math.PI * 2);
          c.fillStyle = glowGrad;
          c.fill();
        }

        // Search highlight ring
        if (isSearchHit) {
          c.beginPath();
          c.arc(node.x, node.y, r + 5, 0, Math.PI * 2);
          c.strokeStyle = '#fbbf24';
          c.lineWidth = 2;
          c.stroke();
        }

        // Node shape
        const alpha = dimmed ? 0.2 : 1;
        const shape = NODE_TYPE_META[node.type]?.shape ?? 'circle';

        c.beginPath();
        if (shape === 'diamond') {
          c.moveTo(node.x, node.y - r);
          c.lineTo(node.x + r, node.y);
          c.lineTo(node.x, node.y + r);
          c.lineTo(node.x - r, node.y);
          c.closePath();
        } else if (shape === 'hex') {
          for (let i = 0; i < 6; i++) {
            const angle = (Math.PI / 3) * i - Math.PI / 6;
            const hx = node.x + r * Math.cos(angle);
            const hy = node.y + r * Math.sin(angle);
            i === 0 ? c.moveTo(hx, hy) : c.lineTo(hx, hy);
          }
          c.closePath();
        } else {
          c.arc(node.x, node.y, r, 0, Math.PI * 2);
        }

        // Fill with gradient
        const fillGrad = c.createRadialGradient(
          node.x - r * 0.3, node.y - r * 0.3, 0,
          node.x, node.y, r * 1.2,
        );
        fillGrad.addColorStop(0, rgbaStr(node.colour, alpha));
        fillGrad.addColorStop(1, rgbaStr(node.colour, alpha * 0.6));
        c.fillStyle = fillGrad;
        c.fill();

        // Border
        if (emphasis) {
          c.strokeStyle = '#ffffff';
          c.lineWidth = 2;
          c.stroke();
        } else if (!dimmed) {
          c.strokeStyle = rgbaStr(node.colour, 0.4);
          c.lineWidth = 1;
          c.stroke();
        }

        // Inner icon for agents
        if (node.type === 'agent') {
          c.font = `bold ${r * 0.7}px ${typography.fontFamily}`;
          c.fillStyle = rgbaStr('#ffffff', alpha * 0.9);
          c.textAlign = 'center';
          c.textBaseline = 'middle';
          const icons: Record<string, string> = {
            finance: '£', content: '✎', education: '▮', research: '◈', health: '♥',
          };
          c.fillText(icons[node.id] ?? '●', node.x, node.y + 1);
        }

        // Label
        const labelAlpha = dimmed ? 0.15 : (emphasis ? 1 : 0.7);
        const fontSize = node.type === 'agent' ? 11 : 9;
        c.font = `${emphasis ? 'bold ' : ''}${fontSize}px ${typography.fontFamily}`;
        c.fillStyle = rgbaStr(colors.text.primary, labelAlpha);
        c.textAlign = 'center';
        c.textBaseline = 'top';

        const labelText = node.label.length > 22 ? node.label.slice(0, 20) + '…' : node.label;
        c.fillText(labelText, node.x, node.y + r + 4);
      }

      c.restore();

      // Zoom indicator
      c.font = `10px ${typography.fontFamily}`;
      c.fillStyle = colors.text.muted;
      c.textAlign = 'right';
      c.fillText(`${Math.round(cam.zoom * 100)}%`, w - 12, h - 10);
    }

    /* ── Animation loop ───────────────────────────────────────────── */

    function loop() {
      simulate();
      draw();
      animFrameRef.current = requestAnimationFrame(loop);
    }
    loop();

    /* ── Mouse interaction ────────────────────────────────────────── */

    function screenToWorld(sx: number, sy: number): { wx: number; wy: number } {
      const cam = cameraRef.current;
      const w2 = width() / 2;
      const h2 = height() / 2;
      const wx = (sx - w2) / cam.zoom + w2 - cam.x;
      const wy = (sy - h2) / cam.zoom + h2 - cam.y;
      return { wx, wy };
    }

    function hitTest(mx: number, my: number): GraphNode | null {
      const { wx, wy } = screenToWorld(mx, my);
      // Reverse order so top-rendered nodes are hit first
      for (let i = nodes.length - 1; i >= 0; i--) {
        const node = nodes[i];
        if (!isNodeVisible(node)) continue;
        const r = getRadius(node) + 4;
        const dx = wx - node.x;
        const dy = wy - node.y;
        if (dx * dx + dy * dy < r * r) return node;
      }
      return null;
    }

    function onMouseDown(e: MouseEvent) {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const hit = hitTest(mx, my);

      if (hit) {
        dragRef.current = {
          node: hit,
          offsetX: mx,
          offsetY: my,
          isPan: false,
        };
        hit.pinned = true;
        tickRef.current = Math.min(tickRef.current, SIM_ITERATIONS - 50); // Reheat briefly
      } else {
        dragRef.current = {
          node: null,
          offsetX: mx,
          offsetY: my,
          isPan: true,
        };
      }
    }

    function onMouseMove(e: MouseEvent) {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const drag = dragRef.current;

      if (drag.isPan) {
        const dx = mx - drag.offsetX;
        const dy = my - drag.offsetY;
        cameraRef.current.x += dx / cameraRef.current.zoom;
        cameraRef.current.y += dy / cameraRef.current.zoom;
        drag.offsetX = mx;
        drag.offsetY = my;
        canvas.style.cursor = 'grabbing';
        return;
      }

      if (drag.node) {
        const { wx, wy } = screenToWorld(mx, my);
        drag.node.x = wx;
        drag.node.y = wy;
        drag.node.vx = 0;
        drag.node.vy = 0;
        canvas.style.cursor = 'grabbing';
        return;
      }

      // Hover detection
      const hit = hitTest(mx, my);
      if (hit) {
        canvas.style.cursor = 'pointer';
        setHoveredNode(hit);
        setTooltipPos({ x: e.clientX, y: e.clientY });
      } else {
        canvas.style.cursor = 'grab';
        setHoveredNode(null);
        setTooltipPos(null);
      }
    }

    function onMouseUp() {
      const drag = dragRef.current;
      if (drag.node) {
        drag.node.pinned = false;
      }
      dragRef.current = { node: null, offsetX: 0, offsetY: 0, isPan: false };
      canvas.style.cursor = 'grab';
    }

    function onClick(e: MouseEvent) {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const hit = hitTest(mx, my);

      if (hit) {
        setSelectedNode(prev => prev?.id === hit.id ? null : hit);
      } else {
        setSelectedNode(null);
      }
    }

    function onWheel(e: WheelEvent) {
      e.preventDefault();
      const cam = cameraRef.current;
      const factor = e.deltaY > 0 ? 0.92 : 1.08;
      cam.zoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, cam.zoom * factor));
    }

    function onDblClick(e: MouseEvent) {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const hit = hitTest(mx, my);

      if (hit) {
        // Zoom to node
        const cam = cameraRef.current;
        cam.zoom = 2.0;
        cam.x = hit.x - width() / 2;
        cam.y = hit.y - height() / 2;
        setSelectedNode(hit);
      } else {
        // Reset view
        cameraRef.current = { x: 0, y: 0, zoom: 1 };
        setSelectedNode(null);
      }
    }

    canvas.addEventListener('mousedown', onMouseDown);
    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mouseup', onMouseUp);
    canvas.addEventListener('click', onClick);
    canvas.addEventListener('dblclick', onDblClick);
    canvas.addEventListener('wheel', onWheel, { passive: false });
    canvas.style.cursor = 'grab';

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      canvas.removeEventListener('mousedown', onMouseDown);
      canvas.removeEventListener('mousemove', onMouseMove);
      canvas.removeEventListener('mouseup', onMouseUp);
      canvas.removeEventListener('click', onClick);
      canvas.removeEventListener('dblclick', onDblClick);
      canvas.removeEventListener('wheel', onWheel);
    };
  }, [data]);

  /* ── Filter toggle ────────────────────────────────────────────── */

  const toggleFilter = useCallback((type: string) => {
    setActiveFilters(prev => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  }, []);

  const clearFilters = useCallback(() => {
    setActiveFilters(new Set());
    setSearchQuery('');
    setSelectedNode(null);
  }, []);

  /* ── Render ───────────────────────────────────────────────────── */

  const nodeTypes: string[] = data?.node_types ?? [];
  const hasData = data?.nodes?.length > 0;

  return (
    <div ref={containerRef} style={{
      backgroundColor: colors.bg.secondary,
      borderRadius: 12,
      border: `1px solid ${colors.border.subtle}`,
      overflow: 'hidden',
      gridColumn: '1 / -1',  // Full width
    }}>
      {/* ── Toolbar ─────────────────────────────────────────────── */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '12px 16px',
        borderBottom: `1px solid ${colors.border.subtle}`,
        flexWrap: 'wrap',
      }}>
        <h3 style={{
          fontSize: typography.sizes.h3,
          fontWeight: typography.weights.semibold,
          color: colors.text.primary,
          margin: 0,
          marginRight: 8,
        }}>
          Knowledge Graph
        </h3>

        {/* Search */}
        <div style={{ position: 'relative', flex: '0 0 220px' }}>
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search nodes…"
            style={{
              width: '100%',
              padding: '6px 10px 6px 28px',
              borderRadius: 6,
              border: `1px solid ${colors.border.default}`,
              backgroundColor: colors.bg.primary,
              color: colors.text.primary,
              fontSize: typography.sizes.small,
              fontFamily: typography.fontFamily,
              outline: 'none',
            }}
          />
          <span style={{
            position: 'absolute',
            left: 8,
            top: '50%',
            transform: 'translateY(-50%)',
            color: colors.text.muted,
            fontSize: '12px',
            pointerEvents: 'none',
          }}>⌕</span>
        </div>

        {/* Node type filter pills */}
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {nodeTypes.map(type => {
            const meta = NODE_TYPE_META[type];
            const isActive = activeFilters.size === 0 || activeFilters.has(type);
            return (
              <button
                key={type}
                onClick={() => toggleFilter(type)}
                style={{
                  padding: '3px 10px',
                  borderRadius: 12,
                  border: `1px solid ${isActive ? colors.accent.teal + '60' : colors.border.subtle}`,
                  backgroundColor: isActive ? colors.bg.tertiary : 'transparent',
                  color: isActive ? colors.text.primary : colors.text.muted,
                  fontSize: typography.sizes.xs,
                  fontFamily: typography.fontFamily,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {meta?.label ?? type}
              </button>
            );
          })}
          {(activeFilters.size > 0 || searchQuery) && (
            <button
              onClick={clearFilters}
              style={{
                padding: '3px 10px',
                borderRadius: 12,
                border: 'none',
                backgroundColor: colors.status.error + '20',
                color: colors.status.error,
                fontSize: typography.sizes.xs,
                fontFamily: typography.fontFamily,
                cursor: 'pointer',
              }}
            >
              Clear
            </button>
          )}
        </div>

        {/* Stats */}
        <div style={{ marginLeft: 'auto', fontSize: typography.sizes.xs, color: colors.text.muted }}>
          {data?.stats?.total_nodes ?? 0} nodes · {data?.stats?.total_edges ?? 0} edges
        </div>
      </div>

      {/* ── Canvas + Detail Panel ───────────────────────────────── */}
      <div style={{ display: 'flex', position: 'relative' }}>
        {/* Canvas */}
        <div style={{ flex: 1, position: 'relative' }}>
          {!hasData ? (
            <div style={{
              height: 520,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <p style={{ color: colors.text.muted, fontSize: typography.sizes.small }}>
                No graph data yet. Run a morning briefing to populate.
              </p>
            </div>
          ) : (
            <canvas ref={canvasRef} style={{ display: 'block' }} />
          )}

          {/* Help text */}
          <div style={{
            position: 'absolute',
            bottom: 8,
            left: 12,
            fontSize: typography.sizes.xs,
            color: colors.text.muted,
            pointerEvents: 'none',
          }}>
            Scroll to zoom · Drag to pan · Click node to inspect · Double-click to focus
          </div>
        </div>

        {/* Detail panel (slides in when node selected) */}
        {selectedNode && (
          <div style={{
            width: 260,
            backgroundColor: colors.bg.tertiary,
            borderLeft: `1px solid ${colors.border.subtle}`,
            padding: 16,
            overflowY: 'auto',
            maxHeight: 520,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 12 }}>
              <div style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: selectedNode.colour,
                boxShadow: `0 0 8px ${selectedNode.colour}`,
                marginTop: 4,
                flexShrink: 0,
              }} />
              <button
                onClick={() => setSelectedNode(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: colors.text.muted,
                  cursor: 'pointer',
                  fontSize: 16,
                  padding: 0,
                  fontFamily: typography.fontFamily,
                }}
              >×</button>
            </div>

            <h4 style={{
              fontSize: typography.sizes.h3,
              fontWeight: typography.weights.semibold,
              color: selectedNode.colour,
              margin: '0 0 4px',
            }}>
              {selectedNode.label}
            </h4>

            <p style={{
              fontSize: typography.sizes.xs,
              color: colors.text.muted,
              margin: '0 0 12px',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}>
              {NODE_TYPE_META[selectedNode.type]?.label ?? selectedNode.type} · {selectedNode.category}
            </p>

            {selectedNode.description && (
              <p style={{
                fontSize: typography.sizes.body,
                color: colors.text.secondary,
                margin: '0 0 12px',
                lineHeight: 1.5,
              }}>
                {selectedNode.description}
              </p>
            )}

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 8,
              marginTop: 8,
            }}>
              <StatBox label="Importance" value={`${selectedNode.importance}/10`} />
              <StatBox label="Connections" value={`${selectedNode.connections ?? 0}`} />
            </div>

            {/* Connected nodes */}
            <div style={{ marginTop: 16 }}>
              <p style={{
                fontSize: typography.sizes.xs,
                color: colors.text.muted,
                fontWeight: typography.weights.medium,
                marginBottom: 6,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}>
                Connections
              </p>
              {edgesRef.current
                .filter(e => e.source === selectedNode.id || e.target === selectedNode.id)
                .slice(0, 8)
                .map(e => {
                  const otherId = e.source === selectedNode.id ? e.target : e.source;
                  const other = nodesRef.current.find(n => n.id === otherId);
                  if (!other) return null;
                  return (
                    <div
                      key={e.id}
                      onClick={() => setSelectedNode(other)}
                      style={{
                        padding: '6px 8px',
                        backgroundColor: colors.bg.secondary,
                        borderRadius: 6,
                        marginBottom: 4,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        transition: 'background-color 0.15s',
                      }}
                    >
                      <div style={{
                        width: 6,
                        height: 6,
                        borderRadius: '50%',
                        backgroundColor: other.colour,
                        flexShrink: 0,
                      }} />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <p style={{
                          margin: 0,
                          fontSize: typography.sizes.small,
                          color: colors.text.primary,
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}>
                          {other.label}
                        </p>
                        <p style={{ margin: 0, fontSize: typography.sizes.xs, color: colors.text.muted }}>
                          {e.relation}
                        </p>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}
      </div>

      {/* ── Floating tooltip ────────────────────────────────────── */}
      {hoveredNode && tooltipPos && !selectedNode && (
        <div style={{
          position: 'fixed',
          left: tooltipPos.x + 14,
          top: tooltipPos.y - 10,
          padding: '8px 12px',
          backgroundColor: colors.bg.tertiary,
          color: colors.text.primary,
          fontSize: typography.sizes.small,
          borderRadius: 8,
          border: `1px solid ${hoveredNode.colour}40`,
          boxShadow: `0 4px 20px ${colors.bg.primary}cc`,
          pointerEvents: 'none',
          zIndex: 300,
          maxWidth: 260,
        }}>
          <p style={{
            margin: '0 0 2px',
            fontWeight: typography.weights.semibold,
            color: hoveredNode.colour,
          }}>
            {hoveredNode.label}
          </p>
          <p style={{ margin: 0, fontSize: typography.sizes.xs, color: colors.text.muted }}>
            {NODE_TYPE_META[hoveredNode.type]?.label ?? hoveredNode.type}
          </p>
          {hoveredNode.description && (
            <p style={{ margin: '4px 0 0', fontSize: typography.sizes.xs, color: colors.text.secondary }}>
              {hoveredNode.description}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Utility sub-components ─────────────────────────────────────── */

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div style={{
      padding: '8px',
      backgroundColor: colors.bg.secondary,
      borderRadius: 6,
      textAlign: 'center',
    }}>
      <p style={{ margin: 0, fontSize: typography.sizes.xs, color: colors.text.muted }}>{label}</p>
      <p style={{
        margin: '2px 0 0',
        fontSize: typography.sizes.h3,
        fontWeight: typography.weights.semibold,
        color: colors.text.primary,
      }}>{value}</p>
    </div>
  );
}

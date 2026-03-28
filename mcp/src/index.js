#!/usr/bin/env node
/**
 * MCP V Enterprise Server — Semantic Filesystem Edition
 *
 * Bridges Claude Code to Obsidian knowledge base with OpenViking-inspired
 * tiered context loading (L0/L1/L2), hierarchical tree navigation,
 * recursive directory search, and session management.
 *
 * Original Tools (backwards compatible):
 *   fetch_knowledge      — Read a document from the KB (L2)
 *   crystallize_learning  — Save an insight/decision to the KB
 *   validate_compliance   — Check content against compliance standards
 *   search_knowledge      — Full-text search across the KB
 *   get_pipeline_status   — Read enterprise pipeline status
 *
 * New Semantic Tools:
 *   abstract             — Read L0 abstract (~100 tokens)
 *   overview             — Read L1 overview (~2K tokens)
 *   tree                 — Hierarchical directory view with L0 annotations
 *   ls                   — List directory contents with L0 summaries
 *   save_memory          — Persist a memory to user/ or agent/ scope
 *   commit_session       — Archive conversation + save session context
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { KBHandler } from "./kb-handler.js";
import { formatADR, formatLearning, formatDecision, formatComplianceReport } from "./templates.js";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------
const OBSIDIAN_PATH = process.env.OBSIDIAN_PATH || `${process.env.HOME}/Desktop/SecondBrain/AgentForce`;
const ENTERPRISE_REPO = process.env.ENTERPRISE_REPO || `${process.env.HOME}/repos/v-enterprise-architecture`;
const KB_TYPE = process.env.KB_TYPE || "obsidian";

const kb = new KBHandler(OBSIDIAN_PATH);

// ---------------------------------------------------------------------------
// Server
// ---------------------------------------------------------------------------
const server = new McpServer({
  name: "mcp-v-enterprise-server",
  version: "2.0.0",
});

// ===========================================================================
// SEMANTIC FILESYSTEM TOOLS (NEW — OpenViking-inspired)
// ===========================================================================

// ---------------------------------------------------------------------------
// L0: Abstract — quick relevance check (~100 tokens)
// ---------------------------------------------------------------------------
server.tool(
  "abstract",
  "Read the L0 abstract (~100 tokens) for a directory. Use this FIRST to check relevance before loading full content. Supports viking:// URIs or relative paths.",
  {
    uri: z.string().describe("Directory path (e.g., 'resources/enterprise-pipeline' or 'viking://user/memories')"),
  },
  async ({ uri }) => {
    try {
      const result = kb.abstract(uri);
      if (result) {
        return { content: [{ type: "text", text: `L0 Abstract for ${uri}:\n${result}` }] };
      }
      return { content: [{ type: "text", text: `No abstract found for: ${uri}` }], isError: true };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ---------------------------------------------------------------------------
// L1: Overview — structural understanding (~2K tokens)
// ---------------------------------------------------------------------------
server.tool(
  "overview",
  "Read the L1 overview (~2K tokens) for a directory. Use AFTER abstract confirms relevance. Contains navigation hints to child content.",
  {
    uri: z.string().describe("Directory path (e.g., 'resources/enterprise-pipeline' or 'viking://agent/memories')"),
  },
  async ({ uri }) => {
    try {
      const result = kb.overview(uri);
      if (result) {
        return { content: [{ type: "text", text: result }] };
      }
      return { content: [{ type: "text", text: `No overview found for: ${uri}` }], isError: true };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ---------------------------------------------------------------------------
// Tree: Hierarchical view with L0 annotations
// ---------------------------------------------------------------------------
server.tool(
  "tree",
  "Show hierarchical directory structure with L0 abstract annotations. Navigate the semantic filesystem to find relevant content before reading.",
  {
    uri: z.string().optional().describe("Root directory (default: entire vault). E.g., 'resources' or 'agent/memories'"),
    depth: z.number().optional().default(3).describe("Maximum depth to show (default: 3)"),
  },
  async ({ uri, depth }) => {
    try {
      const result = kb.tree(uri || "", depth || 3);
      return { content: [{ type: "text", text: `Semantic Filesystem Tree:\n\n${result}` }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ---------------------------------------------------------------------------
// LS: List directory with L0 summaries
// ---------------------------------------------------------------------------
server.tool(
  "ls",
  "List directory contents with L0 abstracts for each subdirectory. Use for navigating the semantic filesystem.",
  {
    uri: z.string().optional().describe("Directory to list (default: root). E.g., 'resources' or 'user/memories'"),
  },
  async ({ uri }) => {
    try {
      const entries = kb.ls(uri || "");
      if (entries.length === 0) {
        return { content: [{ type: "text", text: `Empty or not found: ${uri || "root"}` }] };
      }
      const formatted = entries.map(e => {
        const icon = e.type === "directory" ? "📁" : "📄";
        const abstract = e.abstract ? ` — ${e.abstract}` : "";
        return `${icon} ${e.name}${e.type === "directory" ? "/" : ""}${abstract}`;
      }).join("\n");
      return { content: [{ type: "text", text: formatted }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ---------------------------------------------------------------------------
// Save Memory: persist to user or agent memory
// ---------------------------------------------------------------------------
server.tool(
  "save_memory",
  "Save a memory to the semantic filesystem. Memories are auto-searchable in future sessions. Use for preferences, entities, events, cases, or patterns.",
  {
    scope: z.enum(["user", "agent"]).describe("Memory scope: 'user' (personal) or 'agent' (learned intelligence)"),
    category: z.enum(["preferences", "entities", "events", "cases", "patterns"]).describe("Memory category"),
    name: z.string().describe("Memory name (used as filename)"),
    content: z.string().describe("Memory content in markdown"),
  },
  async ({ scope, category, name, content }) => {
    try {
      const filePath = kb.saveMemory(scope, category, name, content);
      return { content: [{ type: "text", text: `Memory saved: ${filePath}` }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ---------------------------------------------------------------------------
// Commit Session: archive conversation
// ---------------------------------------------------------------------------
server.tool(
  "commit_session",
  "Archive a conversation session with summary. Extracts L0 abstract and L1 overview for future retrieval.",
  {
    session_id: z.string().describe("Unique session identifier (e.g., '2026-03-28-kidsvid-planning')"),
    messages: z.array(z.object({
      role: z.string(),
      content: z.string(),
    })).describe("Conversation messages to archive"),
    abstract: z.string().describe("One-sentence summary of the session (~100 tokens)"),
    overview: z.string().optional().describe("Structural overview of what was discussed (~2K tokens)"),
  },
  async ({ session_id, messages, abstract, overview }) => {
    try {
      const sessionDir = kb.commitSession(session_id, messages, abstract, overview);
      return { content: [{ type: "text", text: `Session archived: ${sessionDir}` }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ===========================================================================
// ORIGINAL TOOLS (backwards compatible)
// ===========================================================================

// ---------------------------------------------------------------------------
// Tool 1: fetch_knowledge (L2 — full document read)
// ---------------------------------------------------------------------------
server.tool(
  "fetch_knowledge",
  "Fetch a full document (L2) from the knowledge base. Searches all directories including semantic filesystem. Use abstract/overview first for relevance check.",
  {
    doc_name: z.string().describe("Document name (without .md extension)"),
    folder: z.string().optional().describe("Specific folder to search. Omit to search all."),
  },
  async ({ doc_name, folder }) => {
    try {
      const result = kb.read(doc_name, folder);
      if (result) {
        return { content: [{ type: "text", text: result.content }] };
      }
      return { content: [{ type: "text", text: `Document not found: ${doc_name}` }], isError: true };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ---------------------------------------------------------------------------
// Tool 2: crystallize_learning
// ---------------------------------------------------------------------------
server.tool(
  "crystallize_learning",
  "Save a learning, decision, or ADR to the knowledge base. For structured memories (preferences, cases, patterns), use save_memory instead.",
  {
    topic: z.string().describe("Title/topic of the learning (used as filename)"),
    content: z.string().describe("The insight, decision, or learning content"),
    format: z.enum(["adr", "learning", "decision"]).default("learning").describe("Format template to use"),
  },
  async ({ topic, content, format }) => {
    try {
      const folder = format === "adr" ? "ADRs" : "Learnings";
      let formatted;
      if (format === "adr") formatted = formatADR(topic, content);
      else if (format === "learning") formatted = formatLearning(topic, content);
      else formatted = formatDecision(topic, content);

      const filePath = kb.write(folder, topic, formatted);
      return { content: [{ type: "text", text: `Saved to ${filePath}` }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ---------------------------------------------------------------------------
// Tool 3: validate_compliance
// ---------------------------------------------------------------------------
server.tool(
  "validate_compliance",
  "Validate content against enterprise compliance standards from the knowledge base.",
  {
    content: z.string().describe("Content to validate"),
    standard: z.string().optional().describe("Specific standard to check against (default: compliance-framework)"),
  },
  async ({ content, standard }) => {
    try {
      const standardName = standard || "compliance-framework";
      const framework = kb.read(standardName, "Standards");
      if (!framework) {
        // Try new location
        const newFramework = kb.read(standardName, "resources/standards");
        if (!newFramework) {
          return { content: [{ type: "text", text: `Standard not found: ${standardName}` }], isError: true };
        }
        const report = formatComplianceReport(content, newFramework.content);
        return { content: [{ type: "text", text: report }] };
      }
      const report = formatComplianceReport(content, framework.content);
      return { content: [{ type: "text", text: report }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ---------------------------------------------------------------------------
// Tool 4: search_knowledge (now hierarchical)
// ---------------------------------------------------------------------------
server.tool(
  "search_knowledge",
  "Search across the entire knowledge base using hierarchical directory drill-down. Scores results by both content match AND directory context. Returns results with relevance scores.",
  {
    query: z.string().describe("Search query"),
    max_results: z.number().optional().default(10).describe("Maximum results to return"),
  },
  async ({ query, max_results }) => {
    try {
      const results = kb.search(query, max_results);
      if (results.length === 0) {
        return { content: [{ type: "text", text: `No results for: ${query}` }] };
      }
      const formatted = results
        .map((r, i) => {
          const score = r.score !== undefined ? ` (score: ${r.score})` : "";
          const dir = r.directory_context ? ` [${r.directory_context}]` : ` (${r.folder})`;
          return `${i + 1}. **${r.file}**${dir}${score}\n   ...${r.snippet}...`;
        })
        .join("\n\n");
      return { content: [{ type: "text", text: `Found ${results.length} results:\n\n${formatted}` }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ---------------------------------------------------------------------------
// Tool 5: get_pipeline_status
// ---------------------------------------------------------------------------
server.tool(
  "get_pipeline_status",
  "Get the current status of the enterprise data intelligence pipeline.",
  {},
  async () => {
    try {
      const statusPath = `${ENTERPRISE_REPO}/outputs/pipeline-status.json`;
      const { readFileSync, existsSync } = await import("fs");
      if (!existsSync(statusPath)) {
        return { content: [{ type: "text", text: "No pipeline status found. Run: python orchestrator.py --mode with-dashboard" }] };
      }
      const status = JSON.parse(readFileSync(statusPath, "utf-8"));
      const summary = Object.entries(status.builds || {})
        .map(([id, b]) => `  ${id}: ${b.build_name} — ${b.status} (${b.duration?.toFixed(1) || 0}s)`)
        .join("\n");
      return {
        content: [{
          type: "text",
          text: `Pipeline Status (${status.pipeline_mode || "unknown"} mode)\nStarted: ${status.started_at || "N/A"}\n\nBuilds:\n${summary}\n\nCompleted: ${status.summary?.completed || 0}/${status.summary?.total || 0}`
        }]
      };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
const transport = new StdioServerTransport();
await server.connect(transport);

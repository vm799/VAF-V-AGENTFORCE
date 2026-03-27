#!/usr/bin/env node
/**
 * MCP V Enterprise Server
 * Bridges Claude Code to Obsidian/Confluence/SharePoint knowledge bases.
 *
 * Tools:
 *   fetch_knowledge      — Read a document from the KB
 *   crystallize_learning  — Save an insight/decision to the KB
 *   validate_compliance   — Check content against compliance standards
 *   search_knowledge      — Full-text search across the KB
 *   get_pipeline_status   — Read enterprise pipeline status
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
  version: "1.0.0",
});

// ---------------------------------------------------------------------------
// Tool 1: fetch_knowledge
// ---------------------------------------------------------------------------
server.tool(
  "fetch_knowledge",
  "Fetch a document from the knowledge base (Obsidian vault). Searches ADRs, Standards, Learnings, Processes folders.",
  {
    doc_name: z.string().describe("Document name (without .md extension)"),
    folder: z.string().optional().describe("Specific folder to search: ADRs, Standards, Learnings, Processes. Omit to search all."),
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
  "Save a learning, decision, or ADR to the knowledge base. Persists insights from the current session.",
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
        return { content: [{ type: "text", text: `Standard not found: ${standardName}` }], isError: true };
      }
      const report = formatComplianceReport(content, framework.content);
      return { content: [{ type: "text", text: report }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }
);

// ---------------------------------------------------------------------------
// Tool 4: search_knowledge
// ---------------------------------------------------------------------------
server.tool(
  "search_knowledge",
  "Full-text search across the entire knowledge base. Returns matching documents with snippets.",
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
        .map((r, i) => `${i + 1}. **${r.file}** (${r.folder})\n   ...${r.snippet}...`)
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

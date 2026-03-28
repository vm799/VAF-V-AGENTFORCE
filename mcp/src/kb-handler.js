/**
 * Knowledge Base Handler — Semantic Filesystem Edition
 *
 * Tiered context loading (L0/L1/L2), hierarchical tree navigation,
 * recursive directory search, and session management.
 *
 * Based on OpenViking architecture patterns:
 *   - L0 (.abstract.md) ~100 tokens — quick relevance check
 *   - L1 (.overview.md) ~2K tokens — structural understanding
 *   - L2 (full document) unlimited — on-demand detail
 */

import { readFileSync, writeFileSync, readdirSync, mkdirSync, existsSync, statSync } from "fs";
import { join, basename, relative, dirname } from "path";

// Semantic filesystem directories (OpenViking-aligned)
const SEMANTIC_DIRS = ["resources", "user", "agent", "sessions"];

// Legacy directories (backwards compatibility)
const LEGACY_DIRS = ["ADRs", "Standards", "Learnings", "Processes"];

// All searchable directories
const ALL_DIRS = [...SEMANTIC_DIRS, ...LEGACY_DIRS];

export class KBHandler {
  constructor(basePath) {
    this.basePath = basePath;
  }

  // ---------------------------------------------------------------------------
  // L0: Abstract (~100 tokens) — quick relevance check
  // ---------------------------------------------------------------------------
  abstract(uri) {
    const dirPath = this._resolvePath(uri);
    const abstractPath = join(dirPath, ".abstract.md");
    if (existsSync(abstractPath)) {
      return readFileSync(abstractPath, "utf-8").trim();
    }
    // Fallback: generate from first 200 chars of any .md file in dir
    if (existsSync(dirPath) && statSync(dirPath).isDirectory()) {
      const files = readdirSync(dirPath).filter(f => f.endsWith(".md") && !f.startsWith("."));
      if (files.length > 0) {
        const content = readFileSync(join(dirPath, files[0]), "utf-8");
        return content.slice(0, 200).replace(/\n/g, " ").trim() + "...";
      }
    }
    return null;
  }

  // ---------------------------------------------------------------------------
  // L1: Overview (~2K tokens) — structural understanding
  // ---------------------------------------------------------------------------
  overview(uri) {
    const dirPath = this._resolvePath(uri);
    const overviewPath = join(dirPath, ".overview.md");
    if (existsSync(overviewPath)) {
      return readFileSync(overviewPath, "utf-8");
    }
    // Fallback: auto-generate from child abstracts
    if (existsSync(dirPath) && statSync(dirPath).isDirectory()) {
      return this._generateOverview(dirPath);
    }
    return null;
  }

  // ---------------------------------------------------------------------------
  // L2: Full document read (unchanged from original)
  // ---------------------------------------------------------------------------
  read(docName, folder) {
    const searchFolders = folder ? [folder] : [...ALL_DIRS, "."];
    const fileName = docName.endsWith(".md") ? docName : `${docName}.md`;

    for (const f of searchFolders) {
      const filePath = f === "." ? join(this.basePath, fileName) : join(this.basePath, f, fileName);
      if (existsSync(filePath)) {
        return { content: readFileSync(filePath, "utf-8"), path: filePath, folder: f };
      }
    }

    // Recursive search in semantic dirs
    for (const root of SEMANTIC_DIRS) {
      const result = this._findFileRecursive(join(this.basePath, root), fileName);
      if (result) return result;
    }

    // Case-insensitive fallback
    for (const f of searchFolders) {
      const dir = f === "." ? this.basePath : join(this.basePath, f);
      if (!existsSync(dir)) continue;
      const files = readdirSync(dir);
      const match = files.find(file => file.toLowerCase() === fileName.toLowerCase());
      if (match) {
        const filePath = join(dir, match);
        return { content: readFileSync(filePath, "utf-8"), path: filePath, folder: f };
      }
    }

    return null;
  }

  // ---------------------------------------------------------------------------
  // Tree: Hierarchical directory view with L0 annotations
  // ---------------------------------------------------------------------------
  tree(uri, depth = 3) {
    const dirPath = this._resolvePath(uri || "");
    if (!existsSync(dirPath) || !statSync(dirPath).isDirectory()) {
      return `Not a directory: ${uri}`;
    }
    return this._buildTree(dirPath, "", depth, 0);
  }

  // ---------------------------------------------------------------------------
  // List: Directory contents with L0 summaries
  // ---------------------------------------------------------------------------
  ls(uri) {
    const dirPath = this._resolvePath(uri || "");
    if (!existsSync(dirPath) || !statSync(dirPath).isDirectory()) {
      return [];
    }

    const entries = readdirSync(dirPath)
      .filter(f => !f.startsWith("."))
      .map(name => {
        const fullPath = join(dirPath, name);
        const isDir = statSync(fullPath).isDirectory();
        const relPath = relative(this.basePath, fullPath);
        let l0 = null;

        if (isDir) {
          const absPath = join(fullPath, ".abstract.md");
          if (existsSync(absPath)) {
            l0 = readFileSync(absPath, "utf-8").trim();
          }
        }

        return {
          name,
          type: isDir ? "directory" : "file",
          path: relPath,
          abstract: l0,
        };
      });

    return entries;
  }

  // ---------------------------------------------------------------------------
  // Hierarchical Search: recursive directory drill-down
  // ---------------------------------------------------------------------------
  searchHierarchical(query, maxResults = 10) {
    const queryLower = query.toLowerCase();
    const queryWords = queryLower.split(/\s+/).filter(w => w.length > 2);
    const results = [];

    // Step 1: Score all directories by L0 relevance
    const dirScores = this._scoreDirs(this.basePath, queryWords, 0);

    // Step 2: Sort by score, drill into top directories first
    dirScores.sort((a, b) => b.score - a.score);

    // Step 3: Search files in highest-scoring directories
    for (const { dir, score: dirScore } of dirScores) {
      if (results.length >= maxResults) break;

      const files = readdirSync(dir)
        .filter(f => f.endsWith(".md") && !f.startsWith("."));

      for (const file of files) {
        if (results.length >= maxResults) break;
        const filePath = join(dir, file);
        const content = readFileSync(filePath, "utf-8");
        const contentLower = content.toLowerCase();

        // Score: word match count + directory score propagation
        let fileScore = 0;
        for (const word of queryWords) {
          if (contentLower.includes(word)) fileScore++;
          if (file.toLowerCase().includes(word)) fileScore += 2; // filename bonus
        }

        if (fileScore > 0) {
          // Score propagation: 50% file match + 50% directory context
          const finalScore = 0.5 * (fileScore / queryWords.length) + 0.5 * dirScore;

          const idx = contentLower.indexOf(queryWords[0] || queryLower);
          const start = Math.max(0, idx - 80);
          const end = Math.min(content.length, idx + query.length + 80);
          const snippet = content.slice(start, end).replace(/\n/g, " ").trim();

          results.push({
            file: basename(file, ".md"),
            folder: relative(this.basePath, dir),
            snippet,
            path: filePath,
            score: Math.round(finalScore * 100) / 100,
            directory_context: relative(this.basePath, dir),
          });
        }
      }
    }

    // Sort by final score
    results.sort((a, b) => b.score - a.score);
    return results.slice(0, maxResults);
  }

  // ---------------------------------------------------------------------------
  // Legacy flat search (backwards compatibility)
  // ---------------------------------------------------------------------------
  search(query, maxResults = 10) {
    // Try hierarchical first, fall back to flat
    const hierarchical = this.searchHierarchical(query, maxResults);
    if (hierarchical.length > 0) return hierarchical;

    // Flat fallback for legacy directories
    const results = [];
    const queryLower = query.toLowerCase();

    for (const folder of LEGACY_DIRS) {
      const dirPath = join(this.basePath, folder);
      if (!existsSync(dirPath)) continue;
      const files = readdirSync(dirPath).filter(f => f.endsWith(".md"));
      for (const file of files) {
        const filePath = join(dirPath, file);
        const content = readFileSync(filePath, "utf-8");
        if (content.toLowerCase().includes(queryLower)) {
          const idx = content.toLowerCase().indexOf(queryLower);
          const start = Math.max(0, idx - 80);
          const end = Math.min(content.length, idx + query.length + 80);
          const snippet = content.slice(start, end).replace(/\n/g, " ").trim();
          results.push({ file: basename(file, ".md"), folder, snippet, path: filePath });
          if (results.length >= maxResults) return results;
        }
      }
    }
    return results;
  }

  // ---------------------------------------------------------------------------
  // Write (enhanced: supports semantic paths)
  // ---------------------------------------------------------------------------
  write(folder, docName, content) {
    const dirPath = join(this.basePath, folder);
    mkdirSync(dirPath, { recursive: true });
    const fileName = docName.endsWith(".md") ? docName : `${docName}.md`;
    const safeName = fileName.replace(/[^a-zA-Z0-9._-]/g, "-");
    const filePath = join(dirPath, safeName);
    writeFileSync(filePath, content, "utf-8");
    return filePath;
  }

  // ---------------------------------------------------------------------------
  // Commit Session: archive conversation + extract memories
  // ---------------------------------------------------------------------------
  commitSession(sessionId, messages, abstract, overview) {
    const sessionDir = join(this.basePath, "sessions", sessionId);
    mkdirSync(sessionDir, { recursive: true });

    // Write messages
    const messagesPath = join(sessionDir, "messages.jsonl");
    const jsonl = messages.map(m => JSON.stringify(m)).join("\n");
    writeFileSync(messagesPath, jsonl, "utf-8");

    // Write L0
    if (abstract) {
      writeFileSync(join(sessionDir, ".abstract.md"), abstract, "utf-8");
    }

    // Write L1
    if (overview) {
      writeFileSync(join(sessionDir, ".overview.md"), overview, "utf-8");
    }

    return sessionDir;
  }

  // ---------------------------------------------------------------------------
  // Save Memory: persist to user or agent memory directories
  // ---------------------------------------------------------------------------
  saveMemory(scope, category, name, content) {
    // scope: "user" or "agent"
    // category: "preferences", "entities", "events", "cases", "patterns"
    const memDir = join(this.basePath, scope, "memories", category);
    mkdirSync(memDir, { recursive: true });
    const fileName = name.endsWith(".md") ? name : `${name}.md`;
    const safeName = fileName.replace(/[^a-zA-Z0-9._-]/g, "-");
    const filePath = join(memDir, safeName);
    writeFileSync(filePath, content, "utf-8");
    return filePath;
  }

  // ---------------------------------------------------------------------------
  // List (legacy compatibility)
  // ---------------------------------------------------------------------------
  list(folder) {
    const dirPath = join(this.basePath, folder);
    if (!existsSync(dirPath)) return [];
    return readdirSync(dirPath)
      .filter(f => f.endsWith(".md") && !f.startsWith("."))
      .map(f => basename(f, ".md"));
  }

  exists(docName, folder) {
    return this.read(docName, folder) !== null;
  }

  // ---------------------------------------------------------------------------
  // Private: Score directories by L0 relevance to query
  // ---------------------------------------------------------------------------
  _scoreDirs(dirPath, queryWords, parentScore) {
    const results = [];
    if (!existsSync(dirPath) || !statSync(dirPath).isDirectory()) return results;

    const entries = readdirSync(dirPath).filter(f => !f.startsWith("."));

    for (const entry of entries) {
      const fullPath = join(dirPath, entry);
      if (!statSync(fullPath).isDirectory()) continue;

      // Score from L0 abstract
      let score = 0;
      const abstractPath = join(fullPath, ".abstract.md");
      if (existsSync(abstractPath)) {
        const abstractText = readFileSync(abstractPath, "utf-8").toLowerCase();
        for (const word of queryWords) {
          if (abstractText.includes(word)) score += 1;
        }
        score = score / Math.max(queryWords.length, 1);
      }

      // Score from directory name
      const nameLower = entry.toLowerCase();
      for (const word of queryWords) {
        if (nameLower.includes(word)) score += 0.5;
      }

      // Score propagation: 50% own score + 50% parent context
      const finalScore = parentScore > 0
        ? 0.5 * score + 0.5 * parentScore
        : score;

      if (finalScore > 0 || parentScore > 0) {
        results.push({ dir: fullPath, score: finalScore });
      }

      // Recurse into subdirectories
      const childScores = this._scoreDirs(fullPath, queryWords, finalScore);
      results.push(...childScores);
    }

    return results;
  }

  // ---------------------------------------------------------------------------
  // Private: Build tree with L0 annotations
  // ---------------------------------------------------------------------------
  _buildTree(dirPath, prefix, maxDepth, currentDepth) {
    if (currentDepth >= maxDepth) return "";
    let output = "";

    const entries = readdirSync(dirPath)
      .filter(f => !f.startsWith(".") && !f.startsWith("node_modules"))
      .sort();

    for (let i = 0; i < entries.length; i++) {
      const entry = entries[i];
      const fullPath = join(dirPath, entry);
      const isLast = i === entries.length - 1;
      const connector = isLast ? "└── " : "├── ";
      const childPrefix = isLast ? "    " : "│   ";
      const isDir = statSync(fullPath).isDirectory();

      if (isDir) {
        // Get L0 annotation
        const abstractPath = join(fullPath, ".abstract.md");
        let annotation = "";
        if (existsSync(abstractPath)) {
          const text = readFileSync(abstractPath, "utf-8").trim();
          // First 80 chars
          annotation = ` — ${text.slice(0, 80)}${text.length > 80 ? "..." : ""}`;
        }
        output += `${prefix}${connector}${entry}/${annotation}\n`;
        output += this._buildTree(fullPath, prefix + childPrefix, maxDepth, currentDepth + 1);
      } else {
        output += `${prefix}${connector}${entry}\n`;
      }
    }

    return output;
  }

  // ---------------------------------------------------------------------------
  // Private: Auto-generate overview from child abstracts
  // ---------------------------------------------------------------------------
  _generateOverview(dirPath) {
    const entries = readdirSync(dirPath).filter(f => !f.startsWith("."));
    const lines = [`# ${basename(dirPath)}\n`];

    for (const entry of entries) {
      const fullPath = join(dirPath, entry);
      if (statSync(fullPath).isDirectory()) {
        const abstractPath = join(fullPath, ".abstract.md");
        if (existsSync(abstractPath)) {
          const text = readFileSync(abstractPath, "utf-8").trim();
          lines.push(`- **${entry}/** — ${text}`);
        } else {
          lines.push(`- **${entry}/**`);
        }
      } else if (entry.endsWith(".md")) {
        lines.push(`- ${entry}`);
      }
    }

    return lines.join("\n");
  }

  // ---------------------------------------------------------------------------
  // Private: Find file recursively in directory tree
  // ---------------------------------------------------------------------------
  _findFileRecursive(dirPath, fileName) {
    if (!existsSync(dirPath) || !statSync(dirPath).isDirectory()) return null;

    const entries = readdirSync(dirPath);

    // Check current directory
    if (entries.includes(fileName)) {
      const filePath = join(dirPath, fileName);
      return {
        content: readFileSync(filePath, "utf-8"),
        path: filePath,
        folder: relative(this.basePath, dirPath),
      };
    }

    // Recurse into subdirectories
    for (const entry of entries) {
      const fullPath = join(dirPath, entry);
      if (statSync(fullPath).isDirectory() && !entry.startsWith(".")) {
        const result = this._findFileRecursive(fullPath, fileName);
        if (result) return result;
      }
    }

    return null;
  }

  // ---------------------------------------------------------------------------
  // Private: Resolve URI or path to absolute filesystem path
  // ---------------------------------------------------------------------------
  _resolvePath(uri) {
    if (!uri) return this.basePath;
    // Strip viking:// prefix if present
    const cleaned = uri.replace(/^viking:\/\//, "").replace(/^\/+/, "");
    return cleaned ? join(this.basePath, cleaned) : this.basePath;
  }
}

/**
 * Knowledge Base Handler
 * Pure filesystem operations for reading/writing/searching markdown files.
 */

import { readFileSync, writeFileSync, readdirSync, mkdirSync, existsSync } from "fs";
import { join, basename, relative } from "path";

const FOLDERS = ["ADRs", "Standards", "Learnings", "Processes"];

export class KBHandler {
  constructor(basePath) {
    this.basePath = basePath;
  }

  /**
   * Read a document from the knowledge base.
   * @param {string} docName - Document name (without .md)
   * @param {string} [folder] - Specific folder, or searches all
   * @returns {{ content: string, path: string, folder: string } | null}
   */
  read(docName, folder) {
    const searchFolders = folder ? [folder] : [...FOLDERS, "."];
    const fileName = docName.endsWith(".md") ? docName : `${docName}.md`;

    for (const f of searchFolders) {
      const filePath = f === "." ? join(this.basePath, fileName) : join(this.basePath, f, fileName);
      if (existsSync(filePath)) {
        return {
          content: readFileSync(filePath, "utf-8"),
          path: filePath,
          folder: f,
        };
      }
    }

    // Try case-insensitive search
    for (const f of searchFolders) {
      const dir = f === "." ? this.basePath : join(this.basePath, f);
      if (!existsSync(dir)) continue;
      const files = readdirSync(dir);
      const match = files.find(
        (file) => file.toLowerCase() === fileName.toLowerCase()
      );
      if (match) {
        const filePath = join(dir, match);
        return {
          content: readFileSync(filePath, "utf-8"),
          path: filePath,
          folder: f,
        };
      }
    }

    return null;
  }

  /**
   * Write a document to the knowledge base.
   * @param {string} folder - Target folder (ADRs, Standards, Learnings, Processes)
   * @param {string} docName - Document name (without .md)
   * @param {string} content - Markdown content
   * @returns {string} Written file path
   */
  write(folder, docName, content) {
    const dirPath = join(this.basePath, folder);
    mkdirSync(dirPath, { recursive: true });

    const fileName = docName.endsWith(".md") ? docName : `${docName}.md`;
    // Sanitize filename
    const safeName = fileName.replace(/[^a-zA-Z0-9._-]/g, "-");
    const filePath = join(dirPath, safeName);

    writeFileSync(filePath, content, "utf-8");
    return filePath;
  }

  /**
   * Search across all markdown files in the knowledge base.
   * @param {string} query - Search query
   * @param {number} [maxResults=10] - Max results
   * @returns {Array<{ file: string, folder: string, snippet: string, path: string }>}
   */
  search(query, maxResults = 10) {
    const results = [];
    const queryLower = query.toLowerCase();

    for (const folder of FOLDERS) {
      const dirPath = join(this.basePath, folder);
      if (!existsSync(dirPath)) continue;

      const files = readdirSync(dirPath).filter((f) => f.endsWith(".md"));
      for (const file of files) {
        const filePath = join(dirPath, file);
        const content = readFileSync(filePath, "utf-8");

        if (content.toLowerCase().includes(queryLower)) {
          // Extract snippet around first match
          const idx = content.toLowerCase().indexOf(queryLower);
          const start = Math.max(0, idx - 80);
          const end = Math.min(content.length, idx + query.length + 80);
          const snippet = content.slice(start, end).replace(/\n/g, " ").trim();

          results.push({
            file: basename(file, ".md"),
            folder,
            snippet,
            path: filePath,
          });

          if (results.length >= maxResults) return results;
        }
      }
    }

    return results;
  }

  /**
   * List documents in a folder.
   * @param {string} folder
   * @returns {string[]}
   */
  list(folder) {
    const dirPath = join(this.basePath, folder);
    if (!existsSync(dirPath)) return [];
    return readdirSync(dirPath)
      .filter((f) => f.endsWith(".md"))
      .map((f) => basename(f, ".md"));
  }

  /**
   * Check if a document exists.
   * @param {string} docName
   * @param {string} [folder]
   * @returns {boolean}
   */
  exists(docName, folder) {
    return this.read(docName, folder) !== null;
  }
}

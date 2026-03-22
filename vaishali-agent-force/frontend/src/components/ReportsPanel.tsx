import React, { useEffect, useState } from 'react';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';

interface ReportFile {
  name: string;
  path: string;
  type: 'markdown' | 'json' | 'csv' | 'text' | 'pdf';
  size: number;
  modified: number;
}

interface FileContent {
  content: string;
  type: string;
  path: string;
}

interface FileTreeItem {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: FileTreeItem[];
  fileType?: string;
}

const API_BASE = '/api';

export function ReportsPanel() {
  const [files, setFiles] = useState<ReportFile[]>([]);
  const [treeData, setTreeData] = useState<FileTreeItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<ReportFile | null>(null);
  const [content, setContent] = useState<FileContent | null>(null);
  const [loading, setLoading] = useState(false);
  const [contentLoading, setContentLoading] = useState(false);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  // Fetch list of reports
  useEffect(() => {
    const fetchReports = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/reports`);
        if (res.ok) {
          const data = await res.json();
          setFiles(data.files || []);
          buildTree(data.files || []);
        }
      } catch (err) {
        console.error('Error fetching reports:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  // Build hierarchical tree from flat file list
  const buildTree = (fileList: ReportFile[]) => {
    const tree: { [key: string]: FileTreeItem } = {};
    const roots: FileTreeItem[] = [];

    for (const file of fileList) {
      const parts = file.path.split('/');
      let currentPath = '';
      let currentLevel = tree;

      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        currentPath = currentPath ? `${currentPath}/${part}` : part;

        if (i === parts.length - 1) {
          // This is a file
          const fileItem: FileTreeItem = {
            name: part,
            path: file.path,
            type: 'file',
            fileType: file.type,
          };
          if (!currentLevel[currentPath]) {
            currentLevel[currentPath] = fileItem;
          }
        } else {
          // This is a folder
          if (!currentLevel[currentPath]) {
            const folderItem: FileTreeItem = {
              name: part,
              path: currentPath,
              type: 'folder',
              children: [],
            };
            currentLevel[currentPath] = folderItem;
            if (i === 0) {
              roots.push(folderItem);
            }
          }

          if (!currentLevel[currentPath].children) {
            currentLevel[currentPath].children = [];
          }
          const children = currentLevel[currentPath].children;
          currentLevel = children ? children.reduce(
            (acc, child) => {
              const childPath = child.path;
              acc[childPath] = child;
              return acc;
            },
            {} as { [key: string]: FileTreeItem }
          ) : {};
        }
      }
    }

    // Populate children arrays properly
    const populateChildren = (items: FileTreeItem[]) => {
      for (const item of items) {
        if (item.type === 'folder' && item.children) {
          item.children.sort((a, b) => {
            // Folders first, then files
            if (a.type !== b.type) return a.type === 'folder' ? -1 : 1;
            return a.name.localeCompare(b.name);
          });
          populateChildren(item.children);
        }
      }
    };

    populateChildren(roots);
    setTreeData(roots);
  };

  // Fetch file content
  const handleSelectFile = async (file: ReportFile) => {
    setSelectedFile(file);
    setContentLoading(true);
    try {
      const res = await fetch(`${API_BASE}/reports/content?path=${encodeURIComponent(file.path)}`);
      if (res.ok) {
        const data = await res.json();
        setContent(data);
      } else {
        setContent(null);
      }
    } catch (err) {
      console.error('Error fetching content:', err);
      setContent(null);
    } finally {
      setContentLoading(false);
    }
  };

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const getFileIcon = (type?: string): string => {
    switch (type) {
      case 'markdown':
        return '📝';
      case 'json':
        return '🔧';
      case 'csv':
        return '📊';
      case 'text':
        return '📋';
      case 'pdf':
        return '📄';
      default:
        return '📁';
    }
  };

  const renderTree = (items: FileTreeItem[], level: number = 0): React.ReactNode => {
    return items.map((item) => (
      <div key={item.path}>
        <div
          style={{
            ...fileTreeItemStyle,
            paddingLeft: `${12 + level * 16}px`,
            backgroundColor:
              selectedFile?.path === item.path
                ? colors.bg.hover
                : 'transparent',
            cursor: item.type === 'file' ? 'pointer' : 'default',
          }}
          onClick={() => {
            if (item.type === 'file') {
              const file = files.find((f) => f.path === item.path);
              if (file) {
                handleSelectFile(file);
              }
            } else {
              toggleFolder(item.path);
            }
          }}
        >
          <span style={{ marginRight: 6 }}>
            {item.type === 'folder'
              ? expandedFolders.has(item.path)
                ? '▼'
                : '▶'
              : getFileIcon(item.fileType)}
          </span>
          <span>{item.name}</span>
        </div>
        {item.type === 'folder' &&
          item.children &&
          expandedFolders.has(item.path) &&
          renderTree(item.children, level + 1)}
      </div>
    ));
  };

  return (
    <div style={panelContainerStyle}>
      <h2 style={headerStyle}>Reports & Previews</h2>

      <div style={contentContainerStyle}>
        {/* Left sidebar: file tree */}
        <div style={sidebarStyle}>
          <div style={sidebarHeaderStyle}>Files</div>
          {loading ? (
            <div style={loadingStyle}>Loading...</div>
          ) : files.length === 0 ? (
            <div style={emptyStyle}>No reports found</div>
          ) : (
            <div style={fileTreeStyle}>{renderTree(treeData)}</div>
          )}
        </div>

        {/* Right panel: content preview */}
        <div style={previewPanelStyle}>
          {!selectedFile ? (
            <div style={emptyPreviewStyle}>Select a report to preview</div>
          ) : contentLoading ? (
            <div style={loadingStyle}>Loading content...</div>
          ) : !content ? (
            <div style={emptyPreviewStyle}>Error loading content</div>
          ) : (
            <>
              <div style={previewHeaderStyle}>
                <div>
                  <div style={filenameStyle}>{selectedFile.name}</div>
                  <div style={metadataStyle}>
                    {formatFileSize(selectedFile.size)} • Modified{' '}
                    {formatDate(new Date(selectedFile.modified * 1000))}
                  </div>
                </div>
              </div>
              <div style={previewContentStyle}>
                {content.type === 'markdown' && (
                  <MarkdownRenderer content={content.content} />
                )}
                {content.type === 'json' && (
                  <JsonRenderer content={content.content} />
                )}
                {content.type === 'csv' && (
                  <CsvRenderer content={content.content} />
                )}
                {content.type === 'text' && (
                  <TextRenderer content={content.content} />
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Renderers for different file types

function MarkdownRenderer({ content }: { content: string }) {
  const html = parseMarkdown(content);
  return (
    <div
      style={markdownContainerStyle}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

function parseMarkdown(text: string): string {
  let html = text;

  // Code blocks (triple backticks)
  html = html.replace(
    /```(.*?)\n([\s\S]*?)```/g,
    (match, lang, code) =>
      `<pre style="background-color: ${colors.bg.hover}; padding: 12px; border-radius: 4px; overflow-x: auto;"><code>${escapeHtml(code.trim())}</code></pre>`
  );

  // Headers (##, ###, ####)
  html = html.replace(
    /^#### (.*?)$/gm,
    (match, text) =>
      `<h4 style="font-size: ${typography.sizes.body}; font-weight: ${typography.weights.bold}; margin: 16px 0 8px; color: ${colors.text.primary};">${text}</h4>`
  );
  html = html.replace(
    /^### (.*?)$/gm,
    (match, text) =>
      `<h3 style="font-size: ${typography.sizes.h3}; font-weight: ${typography.weights.bold}; margin: 16px 0 8px; color: ${colors.accent.teal};">${text}</h3>`
  );
  html = html.replace(
    /^## (.*?)$/gm,
    (match, text) =>
      `<h2 style="font-size: ${typography.sizes.h2}; font-weight: ${typography.weights.bold}; margin: 16px 0 8px; color: ${colors.accent.teal};">${text}</h2>`
  );

  // Bold (**)
  html = html.replace(
    /\*\*(.*?)\*\*/g,
    `<strong style="font-weight: ${typography.weights.bold}; color: ${colors.text.primary};">$1</strong>`
  );

  // Italic (*)
  html = html.replace(
    /\*(.*?)\*/g,
    `<em style="font-style: italic; color: ${colors.text.secondary};">$1</em>`
  );

  // Inline code (backticks)
  html = html.replace(
    /`(.*?)`/g,
    `<code style="background-color: ${colors.bg.hover}; padding: 2px 6px; border-radius: 2px; font-family: monospace; font-size: 0.875em; color: ${colors.accent.teal};">$1</code>`
  );

  // Lists (-)
  html = html.replace(
    /^- (.*?)$/gm,
    `<li style="margin-left: 20px; margin-top: 4px;">$1</li>`
  );
  html = html.replace(
    /(<li.*?<\/li>)/s,
    `<ul style="list-style: disc; margin: 8px 0;">$1</ul>`
  );

  // Line breaks
  html = html.split('\n').join('<br/>');

  return html;
}

function JsonRenderer({ content }: { content: string }) {
  let parsed;
  try {
    parsed = JSON.parse(content);
  } catch {
    return <div style={errorStyle}>Invalid JSON</div>;
  }

  return (
    <pre style={jsonContainerStyle}>
      <code>{syntaxHighlightJson(JSON.stringify(parsed, null, 2))}</code>
    </pre>
  );
}

function syntaxHighlightJson(json: string): string {
  json = json
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match) => {
      let cls = 'number';
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'key';
        } else {
          cls = 'string';
        }
      } else if (/true|false/.test(match)) {
        cls = 'boolean';
      } else if (/null/.test(match)) {
        cls = 'null';
      }
      return `<span style="color: ${getJsonColor(cls)}">${match}</span>`;
    }
  );
}

function getJsonColor(cls: string): string {
  switch (cls) {
    case 'key':
      return '#60a5fa'; // blue
    case 'string':
      return '#4ade80'; // green
    case 'number':
      return '#fb923c'; // orange
    case 'boolean':
      return '#a78bfa'; // purple
    case 'null':
      return '#94a3b8'; // gray
    default:
      return colors.text.primary;
  }
}

function CsvRenderer({ content }: { content: string }) {
  const lines = content.split('\n').filter((line) => line.trim());
  if (lines.length === 0) {
    return <div style={emptyStyle}>Empty CSV file</div>;
  }

  const rows = lines.map((line) =>
    line.split(',').map((cell) => cell.trim())
  );

  return (
    <div style={csvContainerStyle}>
      <table style={tableStyle}>
        <thead>
          <tr>
            {rows[0].map((cell, i) => (
              <th key={i} style={tableHeaderStyle}>
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(1).map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j} style={tableCellStyle}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TextRenderer({ content }: { content: string }) {
  const lines = content.split('\n');
  return (
    <pre style={textContainerStyle}>
      <code>
        {lines.map((line, i) => (
          <div key={i} style={lineStyle}>
            <span style={lineNumberStyle}>{String(i + 1).padStart(4)}</span>
            <span style={lineContentStyle}>{escapeHtml(line)}</span>
          </div>
        ))}
      </code>
    </pre>
  );
}

// Utility functions

function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Styles

const panelContainerStyle: React.CSSProperties = {
  backgroundColor: colors.bg.secondary,
  borderRadius: 12,
  padding: 20,
  border: `1px solid ${colors.border.subtle}`,
  marginTop: 20,
};

const headerStyle: React.CSSProperties = {
  fontSize: typography.sizes.h2,
  fontWeight: typography.weights.semibold,
  color: colors.accent.teal,
  margin: '0 0 16px',
};

const contentContainerStyle: React.CSSProperties = {
  display: 'flex',
  gap: 16,
  height: 600,
  borderRadius: 8,
  overflow: 'hidden',
  border: `1px solid ${colors.border.subtle}`,
};

const sidebarStyle: React.CSSProperties = {
  width: 280,
  backgroundColor: colors.bg.tertiary,
  display: 'flex',
  flexDirection: 'column',
  borderRight: `1px solid ${colors.border.subtle}`,
  overflow: 'hidden',
};

const sidebarHeaderStyle: React.CSSProperties = {
  padding: '12px 16px',
  fontSize: typography.sizes.small,
  fontWeight: typography.weights.semibold,
  color: colors.text.secondary,
  borderBottom: `1px solid ${colors.border.subtle}`,
  flexShrink: 0,
};

const fileTreeStyle: React.CSSProperties = {
  flex: 1,
  overflowY: 'auto',
  overflowX: 'hidden',
  padding: '8px 0',
};

const fileTreeItemStyle: React.CSSProperties = {
  padding: '8px 12px',
  fontSize: typography.sizes.small,
  color: colors.text.primary,
  whiteSpace: 'nowrap',
  textOverflow: 'ellipsis',
  overflow: 'hidden',
  transition: 'background-color 0.2s',
};

const previewPanelStyle: React.CSSProperties = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: colors.bg.tertiary,
  overflow: 'hidden',
};

const previewHeaderStyle: React.CSSProperties = {
  padding: '12px 16px',
  borderBottom: `1px solid ${colors.border.subtle}`,
  flexShrink: 0,
};

const filenameStyle: React.CSSProperties = {
  fontSize: typography.sizes.body,
  fontWeight: typography.weights.semibold,
  color: colors.text.primary,
  margin: '0 0 4px',
};

const metadataStyle: React.CSSProperties = {
  fontSize: typography.sizes.small,
  color: colors.text.secondary,
};

const previewContentStyle: React.CSSProperties = {
  flex: 1,
  overflowY: 'auto',
  padding: 16,
};

const markdownContainerStyle: React.CSSProperties = {
  fontSize: typography.sizes.body,
  lineHeight: 1.6,
  color: colors.text.primary,
};

const jsonContainerStyle: React.CSSProperties = {
  backgroundColor: colors.bg.hover,
  padding: 12,
  borderRadius: 4,
  fontSize: '0.8125rem',
  fontFamily: "'Courier New', monospace",
  color: colors.text.primary,
  overflow: 'auto',
  margin: 0,
};

const csvContainerStyle: React.CSSProperties = {
  overflowX: 'auto',
};

const tableStyle: React.CSSProperties = {
  borderCollapse: 'collapse',
  width: '100%',
  fontSize: typography.sizes.small,
};

const tableHeaderStyle: React.CSSProperties = {
  backgroundColor: colors.bg.hover,
  padding: '8px 12px',
  textAlign: 'left',
  fontWeight: typography.weights.semibold,
  color: colors.accent.teal,
  borderBottom: `1px solid ${colors.border.subtle}`,
};

const tableCellStyle: React.CSSProperties = {
  padding: '8px 12px',
  borderBottom: `1px solid ${colors.border.default}`,
  color: colors.text.primary,
};

const textContainerStyle: React.CSSProperties = {
  backgroundColor: colors.bg.hover,
  padding: 12,
  borderRadius: 4,
  fontSize: '0.8125rem',
  fontFamily: "'Courier New', monospace",
  color: colors.text.primary,
  margin: 0,
  overflow: 'auto',
  lineHeight: 1.5,
};

const lineStyle: React.CSSProperties = {
  display: 'flex',
  gap: 12,
};

const lineNumberStyle: React.CSSProperties = {
  color: colors.text.muted,
  userSelect: 'none',
  minWidth: '40px',
};

const lineContentStyle: React.CSSProperties = {
  flex: 1,
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
};

const emptyStyle: React.CSSProperties = {
  color: colors.text.muted,
  fontSize: typography.sizes.small,
  padding: '16px',
  textAlign: 'center',
};

const loadingStyle: React.CSSProperties = {
  color: colors.text.secondary,
  fontSize: typography.sizes.body,
  padding: '16px',
  textAlign: 'center',
};

const emptyPreviewStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100%',
  color: colors.text.muted,
  fontSize: typography.sizes.body,
};

const errorStyle: React.CSSProperties = {
  color: colors.status.error,
  padding: '16px',
  fontFamily: 'monospace',
};

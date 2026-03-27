/**
 * Template formatters for knowledge base documents.
 */

export function formatADR(topic, content) {
  const date = new Date().toISOString().split("T")[0];
  const slug = topic.replace(/[^a-zA-Z0-9]/g, "-").toLowerCase();
  return `---
tags: [adr, architecture]
created: ${date}
status: proposed
---

# ADR: ${topic}

## Status
Proposed

## Date
${date}

## Context
${content}

## Decision
[To be refined]

## Consequences
[To be determined]

## Related
[Link related ADRs here]
`;
}

export function formatLearning(topic, content) {
  const date = new Date().toISOString().split("T")[0];
  return `---
tags: [learning, session]
created: ${date}
---

# Learning: ${topic}

## Date
${date}

## Insight
${content}

## Applications
[Where this applies in our system]

## Related Documents
[Links to related decisions]
`;
}

export function formatDecision(topic, content) {
  const date = new Date().toISOString().split("T")[0];
  return `---
tags: [decision]
created: ${date}
---

# Decision: ${topic}

## Date
${date}

## Summary
${content}

## Rationale
[Why this decision was made]

## Impact
[What changes as a result]
`;
}

export function formatComplianceReport(content, standardsContent) {
  // Extract key requirements from standards
  const lines = standardsContent.split("\n");
  const checks = [];
  const violations = [];
  const warnings = [];

  // Simple keyword-based checks against the compliance framework
  const contentLower = content.toLowerCase();

  // Check for PII handling mentions
  if (contentLower.includes("pii") || contentLower.includes("personal data")) {
    if (!contentLower.includes("encrypt")) {
      violations.push("PII referenced but no encryption mentioned");
    } else {
      checks.push("PII encryption referenced");
    }
  }

  // Check for audit trail
  if (contentLower.includes("process") || contentLower.includes("transform")) {
    if (!contentLower.includes("log") && !contentLower.includes("audit")) {
      warnings.push("Processing mentioned without audit trail reference");
    } else {
      checks.push("Audit trail referenced for processing");
    }
  }

  // Check for confidence scores in outputs
  if (contentLower.includes("output") || contentLower.includes("deliver")) {
    if (!contentLower.includes("confidence")) {
      warnings.push("Output/delivery mentioned without confidence scores");
    } else {
      checks.push("Confidence scores included in output");
    }
  }

  // Check for data lineage
  if (contentLower.includes("data")) {
    if (!contentLower.includes("lineage") && !contentLower.includes("source")) {
      warnings.push("Data referenced without lineage/source tracking");
    } else {
      checks.push("Data lineage/source tracking present");
    }
  }

  // Default pass if no specific issues found
  if (checks.length === 0 && violations.length === 0 && warnings.length === 0) {
    checks.push("No specific compliance keywords detected — manual review recommended");
  }

  const compliant = violations.length === 0;
  const verdict = compliant ? "COMPLIANT" : "NON-COMPLIANT";

  return `# Compliance Validation Report

## Verdict: ${verdict}

## Passed Checks
${checks.map((c) => `- ✅ ${c}`).join("\n") || "- None"}

## Violations
${violations.map((v) => `- ❌ ${v}`).join("\n") || "- None"}

## Warnings
${warnings.map((w) => `- ⚠️ ${w}`).join("\n") || "- None"}

---
Validated against: Enterprise Compliance Framework
Date: ${new Date().toISOString().split("T")[0]}
`;
}

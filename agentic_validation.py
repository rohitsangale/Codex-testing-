#!/usr/bin/env python3
"""Agentic AI-driven validator for model developer documents.

Usage:
  python agentic_validation.py --input MODEL_DEVELOPER_DOCUMENT.md --output VALIDATION_REPORT.md
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


REQUIRED_SECTIONS = [
    "Overview",
    "Model Architecture",
    "Training Data",
    "Evaluation",
    "Safety & Risk",
    "Limitations",
    "Deployment",
    "Monitoring",
]

KEYWORD_CHECKS = {
    "Safety & Risk": ["risk", "harm", "mitigation", "safety"],
    "Evaluation": ["metric", "benchmark", "test", "result"],
    "Monitoring": ["drift", "incident", "alert", "monitor"],
}


@dataclass
class ValidationFinding:
    category: str
    status: str
    detail: str


def parse_sections(content: str) -> List[Tuple[str, str]]:
    """Return list of (heading, body) for markdown ## headings."""
    headings = list(re.finditer(r"^##\s+(.+)$", content, flags=re.MULTILINE))
    sections: List[Tuple[str, str]] = []
    for i, match in enumerate(headings):
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(content)
        heading = match.group(1).strip()
        body = content[start:end].strip()
        sections.append((heading, body))
    return sections


def validate_document(content: str) -> List[ValidationFinding]:
    findings: List[ValidationFinding] = []
    sections = parse_sections(content)
    section_names = {name for name, _ in sections}

    for required in REQUIRED_SECTIONS:
        if required in section_names:
            findings.append(ValidationFinding("Section Coverage", "PASS", f"Found required section: '{required}'."))
        else:
            findings.append(ValidationFinding("Section Coverage", "FAIL", f"Missing required section: '{required}'."))

    # Content depth checks
    for name, body in sections:
        word_count = len(re.findall(r"\b\w+\b", body))
        if word_count < 40:
            findings.append(
                ValidationFinding(
                    "Content Depth",
                    "WARN",
                    f"Section '{name}' appears brief ({word_count} words). Consider expanding implementation details.",
                )
            )
        else:
            findings.append(
                ValidationFinding(
                    "Content Depth",
                    "PASS",
                    f"Section '{name}' has sufficient detail ({word_count} words).",
                )
            )

    # Domain keyword checks
    section_map = {name: body.lower() for name, body in sections}
    for section_name, keywords in KEYWORD_CHECKS.items():
        body = section_map.get(section_name, "")
        if not body:
            continue
        missing = [kw for kw in keywords if kw not in body]
        if missing:
            findings.append(
                ValidationFinding(
                    "Domain Signals",
                    "WARN",
                    f"Section '{section_name}' is missing domain keywords: {', '.join(missing)}.",
                )
            )
        else:
            findings.append(
                ValidationFinding("Domain Signals", "PASS", f"Section '{section_name}' includes expected domain signals.")
            )

    # Traceability check
    if re.search(r"\[(?:source|ref|citation)\]", content, flags=re.IGNORECASE):
        findings.append(ValidationFinding("Traceability", "PASS", "Document includes explicit source/ref markers."))
    else:
        findings.append(
            ValidationFinding(
                "Traceability",
                "WARN",
                "No explicit [source]/[ref]/[citation] markers found. Add references for data, tests, and decisions.",
            )
        )

    return findings


def render_report(input_path: Path, findings: List[ValidationFinding]) -> str:
    total = len(findings)
    passed = sum(1 for f in findings if f.status == "PASS")
    warnings = sum(1 for f in findings if f.status == "WARN")
    failed = sum(1 for f in findings if f.status == "FAIL")

    lines = [
        "# Validation Report: Model Developer Document",
        "",
        f"**Target document:** `{input_path}`",
        "**Validation mode:** Agentic AI-driven rule orchestration",
        "",
        "## Executive Summary",
        f"- Total checks: **{total}**",
        f"- Passed: **{passed}**",
        f"- Warnings: **{warnings}**",
        f"- Failed: **{failed}**",
        "",
        "## Findings",
        "| Category | Status | Detail |",
        "|---|---|---|",
    ]

    for f in findings:
        emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[f.status]
        lines.append(f"| {f.category} | {emoji} {f.status} | {f.detail} |")

    lines.extend(
        [
            "",
            "## Recommendations",
            "1. Resolve all **FAIL** findings by adding missing core sections.",
            "2. Address **WARN** findings by enriching brief sections with concrete procedures, metrics, and examples.",
            "3. Add formal references to improve traceability and audit-readiness.",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a model developer document and emit a markdown report.")
    parser.add_argument("--input", required=True, help="Path to markdown model developer document")
    parser.add_argument("--output", required=True, help="Path to write markdown validation report")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    content = input_path.read_text(encoding="utf-8")
    findings = validate_document(content)
    report = render_report(input_path, findings)
    output_path.write_text(report, encoding="utf-8")

    print(f"Validation complete. Report written to {output_path}")


if __name__ == "__main__":
    main()

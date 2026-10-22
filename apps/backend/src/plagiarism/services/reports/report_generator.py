"""
Report Generation Service for Hybrid Multilingual Plagiarism Detection Platform.
Generates comprehensive, audit-ready reports in PDF, standalone HTML (offline printable), and JSON formats.
Preserves original evidence scores while reporting reviewer-adjusted metrics.
Supports English, Hindi, and Telugu multilingual text rendering.
"""

from datetime import datetime, timezone
import html
import io
import json
import os
import re
import subprocess
import tempfile
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import shutil

# Auto-register Unicode Indic font if available on host system
_INDIC_FONT_NAME = "Helvetica"
_INDIC_FONT_BOLD = "Helvetica-Bold"
_INDIC_FONT_MONO = "Courier"

_WINDOWS_NIRMALA = r"C:\Windows\Fonts\Nirmala.ttc"
_LINUX_FONTS = [
    ("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", "NotoSans"),
    ("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf", "NotoDevanagari"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans"),
]

if os.path.exists(_WINDOWS_NIRMALA):
    try:
        pdfmetrics.registerFont(TTFont("NirmalaUI", _WINDOWS_NIRMALA, subfontIndex=0))
        pdfmetrics.registerFont(TTFont("NirmalaUIBold", _WINDOWS_NIRMALA, subfontIndex=1))
        _INDIC_FONT_NAME = "NirmalaUI"
        _INDIC_FONT_BOLD = "NirmalaUIBold"
        _INDIC_FONT_MONO = "NirmalaUI"
    except Exception:
        pass
else:
    for reg_path, bold_path, family_name in _LINUX_FONTS:
        if os.path.exists(reg_path):
            try:
                pdfmetrics.registerFont(TTFont(family_name, reg_path))
                bold_name = family_name
                if os.path.exists(bold_path):
                    bold_name = f"{family_name}Bold"
                    pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                _INDIC_FONT_NAME = family_name
                _INDIC_FONT_BOLD = bold_name
                _INDIC_FONT_MONO = family_name
                break
            except Exception:
                pass


def _find_chromium_browser() -> Optional[str]:
    """Finds a Chromium-based browser capable of headless print-to-pdf across Windows and Linux."""
    # Check explicit environment override
    env_browser = os.getenv("CHROMIUM_PATH") or os.getenv("CHROME_BIN")
    if env_browser and os.path.exists(env_browser):
        return env_browser

    # Check Linux/Unix PATH binaries
    for cmd in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "edge", "msedge"):
        found = shutil.which(cmd)
        if found and os.path.exists(found):
            return found

    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\vaibh\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/snap/bin/chromium",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


class ReportGenerator:
    """Generates PDF, HTML, and JSON plagiarism analysis reports."""

    @staticmethod
    def generate_json_report(
        analysis: Dict[str, Any],
        findings: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
        include_notes: bool = True,
        doc_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Builds a comprehensive JSON report payload for external audits and integrations."""
        status_counts = {
            "total": len(findings),
            "unreviewed": 0,
            "keep": 0,
            "exclude": 0,
            "quoted_cited": 0,
            "needs_review": 0,
        }
        for f in findings:
            dec = f.get("review_decision") or "unreviewed"
            status_counts[dec] = status_counts.get(dec, 0) + 1

        reviewed_count = (
            status_counts.get("keep", 0)
            + status_counts.get("exclude", 0)
            + status_counts.get("quoted_cited", 0)
        )
        requiring_review_count = len(findings) - reviewed_count

        cleaned_findings = []
        for idx, f in enumerate(findings, 1):
            item = {
                "finding_number": idx,
                "finding_id": f.get("finding_id"),
                "category": f.get("category"),
                "confidence": f.get("confidence"),
                "submission_start_offset": f.get("submission_start_offset"),
                "submission_end_offset": f.get("submission_end_offset"),
                "submission_excerpt": f.get("submission_excerpt"),
                "reference_document_id": f.get("reference_document_id"),
                "reference_source_title": f.get("reference_source_title"),
                "reference_start_offset": f.get("reference_start_offset"),
                "reference_end_offset": f.get("reference_end_offset"),
                "reference_excerpt": f.get("reference_excerpt"),
                "reference_page_number": f.get("reference_page_number", 1),
                "lexical_similarity": f.get("lexical_similarity", 1.0),
                "semantic_similarity": f.get("semantic_similarity", 0.0),
                "is_quoted": bool(f.get("is_quoted", False)),
                "is_excluded": bool(f.get("is_excluded", False)),
                "review_decision": f.get("review_decision", "unreviewed"),
            }
            if include_notes:
                item["reviewer_notes"] = f.get("reviewer_notes", "")
                item["reviewer_updated_at"] = f.get("reviewer_updated_at")
            cleaned_findings.append(item)

        orig_score = analysis.get("hybrid_evidence_coverage_percent")
        if orig_score is None or orig_score == 0.0:
            orig_score = analysis.get("overall_lexical_coverage_percent", 0.0)

        adj_score = analysis.get("reviewer_adjusted_coverage_percent")
        if adj_score is None:
            adj_score = orig_score

        sub_filename = analysis.get("submission_filename") or (
            doc_meta.get("filename") if doc_meta else "Submitted Document"
        )

        return {
            "report_id": str(analysis.get("analysis_id")),
            "report_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "product_name": "Hybrid Multilingual Plagiarism Detection Platform",
            "analysis_id": str(analysis.get("analysis_id")),
            "submission_filename": sub_filename,
            "mode": analysis.get("mode"),
            "detection_mode": analysis.get("detection_mode", "hybrid"),
            "status": analysis.get("status", "completed"),
            "overall_lexical_coverage_percent": analysis.get("overall_lexical_coverage_percent", 0.0),
            "overall_semantic_coverage_percent": analysis.get("overall_semantic_coverage_percent", 0.0),
            "net_adjusted_score_percent": analysis.get("net_adjusted_score_percent", 0.0),
            "hybrid_evidence_coverage_percent": orig_score,
            "reviewer_adjusted_coverage_percent": adj_score,
            "total_findings": len(findings),
            "total_sources_matched": len(sources),
            "document": {
                "document_id": analysis.get("submission_document_id"),
                "filename": sub_filename,
                "mime_type": doc_meta.get("mime_type") if doc_meta else "application/pdf",
                "detected_language": doc_meta.get("detected_language") if doc_meta else "en",
                "word_count": doc_meta.get("word_count") if doc_meta else None,
                "char_count": doc_meta.get("char_count") if doc_meta else None,
                "page_count": doc_meta.get("page_count") if doc_meta else None,
            },
            "parameters": {
                "mode": analysis.get("mode"),
                "detection_mode": analysis.get("detection_mode", "hybrid"),
            },
            "metrics": {
                "original_evidence_coverage_percent": orig_score,
                "reviewer_adjusted_coverage_percent": adj_score,
                "overall_lexical_coverage_percent": analysis.get("overall_lexical_coverage_percent", 0.0),
                "overall_semantic_coverage_percent": analysis.get("overall_semantic_coverage_percent", 0.0),
                "matched_source_count": len(sources),
                "total_findings_count": len(findings),
                "reviewed_findings_count": reviewed_count,
                "findings_requiring_review_count": requiring_review_count,
                "status_counts": status_counts,
            },
            "sources": sources,
            "findings": cleaned_findings,
            "methodology": {
                "text_matching": "Deterministic Winnowing (k=25, w=16) and BM25 token alignment",
                "meaning_based_matching": "Dense semantic retrieval using multilingual-e5-small embeddings (384d)",
                "combined_analysis": "Non-overlapping interval-union calculation with calibrated scoring",
            },
            "interpretation": (
                f"Analysis completed with {orig_score:.1f}% overall evidence coverage across {len(sources)} reference source(s). "
                f"A total of {len(findings)} matching passage(s) were identified."
            ),
            "disclaimer": (
                "Evidence coverage represents the portion of the submitted text associated with detected similarity evidence. "
                "Similarity alone does not establish academic misconduct or copyright infringement. "
                "Quoted text, citations, and standard terminology must be verified by authorized human reviewers."
            ),
        }

    @staticmethod
    def generate_html_report(
        analysis: Dict[str, Any],
        findings: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
        include_notes: bool = True,
        doc_meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Builds a beautiful, responsive, self-contained HTML report printable with browser print and Edge PDF engine."""
        orig_score = analysis.get("hybrid_evidence_coverage_percent")
        if orig_score is None or orig_score == 0.0:
            orig_score = analysis.get("overall_lexical_coverage_percent", 0.0)

        adj_score = analysis.get("reviewer_adjusted_coverage_percent")
        if adj_score is None:
            adj_score = orig_score

        sub_filename = analysis.get("submission_filename") or (
            doc_meta.get("filename") if doc_meta else "Submitted Document"
        )
        filename_esc = html.escape(sub_filename)
        analysis_id = html.escape(str(analysis.get("analysis_id", "")))
        det_mode_raw = str(analysis.get("detection_mode", "hybrid"))
        det_mode = "Hybrid Balanced" if det_mode_raw == "hybrid" else ("Exact & Structural" if det_mode_raw == "lexical" else "Semantic Paraphrase")
        created_at = html.escape(str(analysis.get("created_at", ""))[:19].replace("T", " "))
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Document information
        doc_format = "PDF" if sub_filename.lower().endswith(".pdf") else ("DOCX" if sub_filename.lower().endswith(".docx") else "TXT")
        detected_lang = doc_meta.get("detected_language") if doc_meta else "en"
        lang_label = "English" if detected_lang == "en" else ("Hindi (हिंदी)" if detected_lang == "hi" else ("Telugu (తెలుగు)" if detected_lang == "te" else detected_lang.upper()))
        word_count = f"{doc_meta.get('word_count'):,}" if (doc_meta and doc_meta.get("word_count")) else "N/A"
        char_count = f"{doc_meta.get('char_count'):,}" if (doc_meta and doc_meta.get("char_count")) else "N/A"
        page_count = str(doc_meta.get("page_count")) if (doc_meta and doc_meta.get("page_count")) else "N/A"

        # Status counts
        status_counts = {"unreviewed": 0, "keep": 0, "exclude": 0, "quoted_cited": 0, "needs_review": 0}
        for f in findings:
            dec = f.get("review_decision") or "unreviewed"
            status_counts[dec] = status_counts.get(dec, 0) + 1

        reviewed_count = status_counts["keep"] + status_counts["exclude"] + status_counts["quoted_cited"]
        requiring_review_count = len(findings) - reviewed_count

        # Sources rows
        sources_rows_html = ""
        for idx, s in enumerate(sources, 1):
            s_title = html.escape(s.get("source_title", "Source"))
            s_lex = s.get("lexical_coverage_percent", 0.0)
            s_sem = s.get("semantic_coverage_percent", 0.0)
            s_passages = s.get("matched_passage_count", 0)
            sources_rows_html += f"""
            <tr style="border-bottom: 1px solid #E2E8F0;">
                <td style="padding: 10px 14px; font-weight: 500; color: #1E293B;">{idx}. {s_title}</td>
                <td style="padding: 10px 14px; text-align: center; color: #475569;">{s_passages}</td>
                <td style="padding: 10px 14px; text-align: center; color: #64748B;">Lexical & Semantic</td>
                <td style="padding: 10px 14px; text-align: right; color: #4F46E5; font-weight: 600;">{max(s_lex, s_sem):.1f}%</td>
            </tr>
            """

        category_labels = {
            "exact_copy": ("Exact Copy", "#DC2626", "#FEE2E2"),
            "near_exact_rewrite": ("Near-Exact", "#D97706", "#FEF3C7"),
            "paraphrase": ("Paraphrase", "#7C3AED", "#EDE9FE"),
            "potential_translation": ("Translation", "#0284C7", "#E0F2FE"),
        }

        decision_labels = {
            "keep": ("Kept (Confirmed)", "#15803D", "#DCFCE7"),
            "exclude": ("Excluded", "#64748B", "#F1F5F9"),
            "quoted_cited": ("Quoted / Cited", "#0369A1", "#E0F2FE"),
            "needs_review": ("Needs Review", "#B45309", "#FEF3C7"),
            "unreviewed": ("Unreviewed (Pending)", "#94A3B8", "#F8FAFC"),
        }

        # Findings cards (Include ALL findings!)
        findings_cards_html = ""
        for idx, f in enumerate(findings, 1):
            cat_key = f.get("category", "")
            cat_info = category_labels.get(cat_key, ("Similarity Match", "#475569", "#F1F5F9"))
            dec_key = f.get("review_decision") or "unreviewed"
            dec_info = decision_labels.get(dec_key, ("Unreviewed (Pending)", "#94A3B8", "#F8FAFC"))
            sub_exc = html.escape((f.get("submission_excerpt") or "").strip())
            ref_exc = html.escape((f.get("reference_excerpt") or "").strip())
            ref_title = html.escape(f.get("reference_source_title", "Reference Document"))
            notes = html.escape(f.get("reviewer_notes", "")) if include_notes else ""

            lex_sim = f.get("lexical_similarity", 1.0)
            sem_sim = f.get("semantic_similarity", 0.0)
            sim_badge = f"Semantic Cosine: {sem_sim:.4f}" if sem_sim > 0 else f"Lexical Similarity: {lex_sim:.2f}"

            notes_html = f"""
            <div style="margin-top: 10px; padding: 8px 12px; background: #EEF2FF; border-left: 3px solid #6366F1; font-size: 12px; color: #3730A3; border-radius: 4px;">
                <strong>Reviewer Note:</strong> {notes}
            </div>
            """ if notes else ""

            findings_cards_html += f"""
            <div style="margin-bottom: 20px; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; background: #FFFFFF; break-inside: avoid; page-break-inside: avoid;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-weight: 700; color: #1E293B; font-size: 14px;">Finding {idx} of {len(findings)}</span>
                        <span style="background: {cat_info[2]}; color: {cat_info[1]}; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 9999px;">{cat_info[0]}</span>
                        <span style="background: {dec_info[2]}; color: {dec_info[1]}; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 9999px;">{dec_info[0]}</span>
                        <span style="font-size: 11px; color: #64748B; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">{sim_badge}</span>
                    </div>
                    <div style="font-size: 12px; color: #64748B;">
                        Source: <strong>{ref_title}</strong> (Offsets: {f.get('submission_start_offset', 0)}–{f.get('submission_end_offset', 0)})
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 8px;">
                    <div style="background: #F8FAFC; padding: 12px; border-radius: 6px; border: 1px solid #E2E8F0;">
                        <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 6px;">Submitted Document Passage</div>
                        <div style="font-size: 12px; color: #1E293B; line-height: 1.5; white-space: pre-wrap; font-family: 'Nirmala UI', -apple-system, sans-serif;">{sub_exc}</div>
                    </div>
                    <div style="background: #F8FAFC; padding: 12px; border-radius: 6px; border: 1px solid #E2E8F0;">
                        <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 6px;">Matching Reference Passage</div>
                        <div style="font-size: 12px; color: #1E293B; line-height: 1.5; white-space: pre-wrap; font-family: 'Nirmala UI', -apple-system, sans-serif;">{ref_exc}</div>
                    </div>
                </div>
                {notes_html}
            </div>
            """

        score_color = "#DC2626" if adj_score >= 40 else ("#D97706" if adj_score >= 15 else "#15803D")
        score_badge = "High Similarity" if adj_score >= 40 else ("Moderate Similarity" if adj_score >= 15 else "Low Similarity")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plagiarism Analysis Report - {filename_esc}</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 15mm;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Nirmala UI', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #F8FAFC;
            color: #1E293B;
            line-height: 1.5;
            padding: 24px 16px;
            font-size: 13px;
        }}
        .report-container {{
            max-width: 960px;
            margin: 0 auto;
            background: #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            padding: 36px;
            border: 1px solid #E2E8F0;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #4F46E5;
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        .brand-title {{
            font-size: 22px;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.5px;
        }}
        .brand-subtitle {{
            font-size: 13px;
            color: #64748B;
            margin-top: 3px;
        }}
        .executive-summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 14px;
            text-align: center;
        }}
        .metric-val {{
            font-size: 26px;
            font-weight: 800;
            margin: 4px 0;
        }}
        .metric-label {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            color: #64748B;
            letter-spacing: 0.5px;
        }}
        .section-title {{
            font-size: 15px;
            font-weight: 700;
            color: #0F172A;
            margin: 24px 0 12px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section-title::before {{
            content: "";
            display: inline-block;
            width: 4px;
            height: 16px;
            background: #4F46E5;
            border-radius: 2px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
        }}
        .info-item {{
            font-size: 12px;
        }}
        .info-label {{
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            font-size: 10px;
        }}
        .info-value {{
            font-weight: 600;
            color: #1E293B;
            margin-top: 2px;
        }}
        .disclaimer-box {{
            background: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 14px;
            font-size: 11px;
            color: #475569;
            margin-top: 28px;
            line-height: 1.5;
        }}
        .print-btn {{
            background: #4F46E5;
            color: #FFFFFF;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .print-btn:hover {{
            background: #4338CA;
        }}
        @media print {{
            body {{ background: #FFFFFF; padding: 0; }}
            .report-container {{ border: none; box-shadow: none; padding: 0; max-width: 100%; }}
            .no-print {{ display: none !important; }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;" class="no-print">
            <button onclick="window.print()" class="print-btn">
                Print / Save as PDF
            </button>
        </div>

        <!-- Section 1: Report Header -->
        <div class="header">
            <div>
                <div class="brand-title">Document Similarity Analysis Report</div>
                <div class="brand-subtitle">Plagiarism Engine — Similarity & Plagiarism Audit Report (Multilingual Detection Platform)</div>
                <div style="margin-top: 10px; font-size: 13px; color: #334155;">
                    Submitted Document: <strong>{filename_esc}</strong>
                </div>
            </div>
            <div style="text-align: right; font-size: 11px; color: #64748B; line-height: 1.6;">
                <div>Analysis ID: <code style="font-family: monospace;">{analysis_id[:12]}...</code></div>
                <div>Analyzed: <strong>{created_at}</strong></div>
                <div>Report Generated: <strong>{generated_at}</strong></div>
                <div>Mode: <strong>{det_mode}</strong></div>
            </div>
        </div>

        <!-- Section 2: Executive Summary -->
        <div class="section-title">1. Executive Summary</div>
        <div class="executive-summary">
            <div class="metric-card">
                <div class="metric-label">Evidence Coverage</div>
                <div class="metric-val" style="color: {score_color};">{orig_score:.1f}%</div>
                <div style="font-size: 11px; font-weight: 600; color: {score_color};">{score_badge}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">After Human Review</div>
                <div class="metric-val" style="color: #4F46E5;">{adj_score:.1f}%</div>
                <div style="font-size: 11px; color: #64748B;">{reviewed_count} of {len(findings)} Reviewed</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Detected Passages</div>
                <div class="metric-val" style="color: #1E293B;">{len(findings)}</div>
                <div style="font-size: 11px; color: #64748B;">{requiring_review_count} Pending Review</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Matching Sources</div>
                <div class="metric-val" style="color: #1E293B;">{len(sources)}</div>
                <div style="font-size: 11px; color: #64748B;">Reference Files</div>
            </div>
        </div>
        <div style="background: #F1F5F9; border-radius: 6px; padding: 10px 14px; font-size: 12px; color: #475569; margin-bottom: 20px;">
            <strong>Interpretation Notice:</strong> Evidence coverage represents the portion of the submitted text associated with detected similarity evidence. Similarity alone does not establish academic misconduct or copyright infringement.
        </div>

        <!-- Section 3: Document Information -->
        <div class="section-title">2. Document Information</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Filename</div>
                <div class="info-value">{filename_esc}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Format & Language</div>
                <div class="info-value">{doc_format} • {lang_label}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Word & Page Count</div>
                <div class="info-value">{word_count} words ({page_count} pages)</div>
            </div>
            <div class="info-item">
                <div class="info-label">Analysis Mode</div>
                <div class="info-value">{det_mode}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Analysis Status</div>
                <div class="info-value" style="color: #15803D; text-transform: uppercase;">Completed</div>
            </div>
            <div class="info-item">
                <div class="info-label">Character Count</div>
                <div class="info-value">{char_count} characters</div>
            </div>
        </div>

        <!-- Section 4: Matched Reference Sources -->
        <div class="section-title">3. Matched Reference Sources ({len(sources)})</div>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 12px; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden;">
            <thead>
                <tr style="background: #F8FAFC; border-bottom: 1px solid #E2E8F0; color: #64748B; text-transform: uppercase; font-size: 10px; letter-spacing: 0.5px;">
                    <th style="padding: 10px 14px; text-align: left;">Reference Document</th>
                    <th style="padding: 10px 14px; text-align: center;">Matching Passages</th>
                    <th style="padding: 10px 14px; text-align: center;">Evidence Type</th>
                    <th style="padding: 10px 14px; text-align: right;">Source Contribution</th>
                </tr>
            </thead>
            <tbody>
                {sources_rows_html if sources_rows_html else '<tr><td colspan="4" style="padding: 16px; text-align: center; color: #94A3B8;">No reference sources matched above threshold.</td></tr>'}
            </tbody>
        </table>

        <!-- Section 5: Detailed Similarity Findings -->
        <div class="section-title">4. Detailed Similarity Findings ({len(findings)} Total Passages)</div>
        <div style="margin-bottom: 24px;">
            {findings_cards_html if findings_cards_html else '<div style="padding: 24px; text-align: center; color: #94A3B8; background: #F8FAFC; border-radius: 8px;">No similarity findings detected above threshold.</div>'}
        </div>

        <!-- Section 6: Reviewer Decisions -->
        <div class="section-title">5. Reviewer Decisions & Audit Summary</div>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
            <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center;">
                <div>
                    <div style="font-size: 18px; font-weight: 700; color: #15803D;">{status_counts['keep']}</div>
                    <div style="font-size: 10px; color: #64748B; text-transform: uppercase;">Kept (Confirmed)</div>
                </div>
                <div>
                    <div style="font-size: 18px; font-weight: 700; color: #64748B;">{status_counts['exclude']}</div>
                    <div style="font-size: 10px; color: #64748B; text-transform: uppercase;">Excluded</div>
                </div>
                <div>
                    <div style="font-size: 18px; font-weight: 700; color: #0369A1;">{status_counts['quoted_cited']}</div>
                    <div style="font-size: 10px; color: #64748B; text-transform: uppercase;">Quoted / Cited</div>
                </div>
                <div>
                    <div style="font-size: 18px; font-weight: 700; color: #B45309;">{status_counts['needs_review']}</div>
                    <div style="font-size: 10px; color: #64748B; text-transform: uppercase;">Needs Review</div>
                </div>
                <div>
                    <div style="font-size: 18px; font-weight: 700; color: #94A3B8;">{status_counts['unreviewed']}</div>
                    <div style="font-size: 10px; color: #64748B; text-transform: uppercase;">Unreviewed</div>
                </div>
            </div>
            <div style="border-top: 1px solid #E2E8F0; margin-top: 12px; padding-top: 12px; display: flex; justify-content: space-between; font-size: 12px;">
                <span>Original Detector Evidence: <strong>{orig_score:.1f}%</strong></span>
                <span>Reviewer-Adjusted Final Score: <strong style="color: {score_color};">{adj_score:.1f}%</strong></span>
            </div>
        </div>

        <!-- Section 7: Interpretation of Results -->
        <div class="section-title">6. Interpretation of Results</div>
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 20px; font-size: 12px; line-height: 1.6; color: #334155;">
            <p>
                This analysis compared the submitted document against {len(sources)} reference source(s) using the {det_mode} engine.
                The system detected <strong>{len(findings)} matching passage(s)</strong> resulting in an overall evidence union coverage of <strong>{orig_score:.1f}%</strong>.
            </p>
            <p style="margin-top: 8px;">
                Identified matches encompass exact verbatim phrasing, structured syntactic rewrites, and semantic paraphrasing.
                High evidence scores often occur when analyzing revisions of existing documents, templates, or shared syllabi.
                Each finding should be evaluated in context to determine whether citations, quotations, or authorized adaptations apply.
            </p>
        </div>

        <!-- Section 8: Methodology -->
        <div class="section-title">7. Methodology</div>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 20px; font-size: 12px; line-height: 1.6; color: #475569;">
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px;">
                <div>
                    <strong style="color: #0F172A;">Text Matching</strong>
                    <p style="margin-top: 4px; font-size: 11px;">Deterministic Winnowing (k=25, w=16) and BM25 token alignment identifying verbatim and near-exact text overlaps.</p>
                </div>
                <div>
                    <strong style="color: #0F172A;">Meaning-Based Matching</strong>
                    <p style="margin-top: 4px; font-size: 11px;">Multilingual neural embeddings (intfloat/multilingual-e5-small, 384d) computing cosine similarity across English, Hindi, and Telugu.</p>
                </div>
                <div>
                    <strong style="color: #0F172A;">Combined Analysis</strong>
                    <p style="margin-top: 4px; font-size: 11px;">Calculates non-overlapping interval union coverage to prevent double counting overlapping lexical and semantic evidence.</p>
                </div>
            </div>
        </div>

        <!-- Section 9: Important Limitations & Disclaimer -->
        <div class="section-title">8. Important Limitations</div>
        <div class="disclaimer-box">
            <strong>Academic Integrity & Legal Disclaimer:</strong>
            This similarity report was generated automatically by the Hybrid Multilingual Plagiarism Detection Platform.
            Similarity scores represent statistical, lexical, and semantic overlaps between digital documents and do not inherently denote academic dishonesty, copyright infringement, or intellectual property misappropriation.
            Properly attributed quotations, common technical terminology, mathematical notation, and boilerplate syllabus definitions can legitimately match reference sources.
            Final determinations must be made by qualified human educators or review boards examining full contextual evidence.
        </div>
    </div>
</body>
</html>
"""
        return html_content

    @staticmethod
    def generate_pdf_report(
        analysis: Dict[str, Any],
        findings: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
        include_notes: bool = True,
        doc_meta: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Builds a formal multi-page PDF audit report.
        Prefers headless Chromium/Edge print-to-pdf for 100% pixel-perfect vector Indic font shaping.
        Seamlessly falls back to robust ReportLab generator if browser engine is unavailable.
        """
        browser_exe = _find_chromium_browser()
        if browser_exe:
            try:
                html_content = ReportGenerator.generate_html_report(
                    analysis=analysis,
                    findings=findings,
                    sources=sources,
                    include_notes=include_notes,
                    doc_meta=doc_meta,
                )
                with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tf:
                    tf.write(html_content)
                    temp_html_path = tf.name

                temp_pdf_path = temp_html_path.replace(".html", ".pdf")
                temp_profile_dir = os.path.join(tempfile.gettempdir(), f"edge_pdf_{os.getpid()}")
                os.makedirs(temp_profile_dir, exist_ok=True)

                cmd = [
                    browser_exe,
                    "--headless=new",
                    "--disable-gpu",
                    f"--user-data-dir={temp_profile_dir}",
                    "--no-sandbox",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={temp_pdf_path}",
                    temp_html_path,
                ]
                subprocess.run(cmd, check=True, timeout=30, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                if os.path.exists(temp_pdf_path) and os.path.getsize(temp_pdf_path) > 0:
                    with open(temp_pdf_path, "rb") as pf:
                        pdf_bytes = pf.read()
                    try:
                        os.remove(temp_html_path)
                        os.remove(temp_pdf_path)
                    except Exception:
                        pass
                    return pdf_bytes
            except Exception:
                # Fall back to ReportLab if browser invocation encounters any issue
                pass

        # Robust ReportLab fallback generator
        return ReportGenerator._generate_pdf_reportlab(
            analysis=analysis,
            findings=findings,
            sources=sources,
            include_notes=include_notes,
            doc_meta=doc_meta,
        )

    @staticmethod
    def _generate_pdf_reportlab(
        analysis: Dict[str, Any],
        findings: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
        include_notes: bool = True,
        doc_meta: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """ReportLab fallback generator engineered to never raise LayoutError on long excerpts."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0F172A"),
            fontName=_INDIC_FONT_BOLD,
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#64748B"),
            fontName=_INDIC_FONT_NAME,
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#1E293B"),
            fontName=_INDIC_FONT_BOLD,
            spaceBefore=12,
            spaceAfter=4,
        )
        cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#1E293B"),
            fontName=_INDIC_FONT_NAME,
        )
        cell_bold = ParagraphStyle(
            "TableCellBold",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#0F172A"),
            fontName=_INDIC_FONT_BOLD,
        )
        excerpt_style = ParagraphStyle(
            "ExcerptStyle",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155"),
            fontName=_INDIC_FONT_NAME,
        )
        disclaimer_style = ParagraphStyle(
            "DisclaimerStyle",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor("#64748B"),
            fontName=_INDIC_FONT_NAME,
        )

        elements = []

        sub_filename = analysis.get("submission_filename") or (
            doc_meta.get("filename") if doc_meta else "Submitted Document"
        )
        analysis_id = str(analysis.get("analysis_id", ""))
        created_at = str(analysis.get("created_at", ""))[:19]

        elements.append(Paragraph("Document Similarity Analysis Report", title_style))
        elements.append(Paragraph(f"Document: {sub_filename} • Analysis ID: {analysis_id[:16]}... • Date: {created_at}", subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4F46E5"), spaceAfter=10))

        orig_score = analysis.get("hybrid_evidence_coverage_percent")
        if orig_score is None or orig_score == 0.0:
            orig_score = analysis.get("overall_lexical_coverage_percent", 0.0)

        adj_score = analysis.get("reviewer_adjusted_coverage_percent")
        if adj_score is None:
            adj_score = orig_score

        metrics_data = [
            [
                Paragraph("<b>Evidence Coverage</b>", cell_style),
                Paragraph(f"<b><font size=12 color='#DC2626'>{orig_score:.1f}%</font></b>", cell_style),
                Paragraph("<b>After Review</b>", cell_style),
                Paragraph(f"<b><font size=12 color='#4F46E5'>{adj_score:.1f}%</font></b>", cell_style),
            ],
            [
                Paragraph("<b>Total Passages</b>", cell_style),
                Paragraph(str(len(findings)), cell_style),
                Paragraph("<b>Matching Sources</b>", cell_style),
                Paragraph(str(len(sources)), cell_style),
            ],
        ]

        metrics_table = Table(metrics_data, colWidths=[2.0 * inch, 1.75 * inch, 2.0 * inch, 1.75 * inch])
        metrics_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ])
        )
        elements.append(metrics_table)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("Matched Reference Sources", h2_style))
        if sources:
            src_header = [
                Paragraph("<b>Reference Source</b>", cell_bold),
                Paragraph("<b>Passages</b>", cell_bold),
                Paragraph("<b>Lexical Cov.</b>", cell_bold),
                Paragraph("<b>Semantic Cov.</b>", cell_bold),
            ]
            src_rows = [src_header]
            for s in sources:
                src_rows.append([
                    Paragraph(s.get("source_title", "Source"), cell_style),
                    Paragraph(str(s.get("matched_passage_count", 0)), cell_style),
                    Paragraph(f"{s.get('lexical_coverage_percent', 0.0):.1f}%", cell_style),
                    Paragraph(f"{s.get('semantic_coverage_percent', 0.0):.1f}%", cell_style),
                ])
            src_table = Table(src_rows, colWidths=[3.5 * inch, 1.3 * inch, 1.3 * inch, 1.4 * inch])
            src_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ])
            )
            elements.append(src_table)
        else:
            elements.append(Paragraph("No reference sources matched above threshold.", cell_style))

        elements.append(Spacer(1, 10))

        elements.append(Paragraph(f"Detailed Matching Findings ({len(findings)})", h2_style))
        if findings:
            for idx, f in enumerate(findings, 1):
                cat = f.get("category", "").replace("_", " ").title()
                dec = (f.get("review_decision") or "unreviewed").replace("_", " ").title()
                src_title = f.get("reference_source_title", "Source")
                sub_txt = (f.get("submission_excerpt") or "").strip()
                ref_txt = (f.get("reference_excerpt") or "").strip()
                note = f.get("reviewer_notes", "").strip() if include_notes else ""

                # Safe XML escaping
                sub_clean = html.escape(sub_txt)
                ref_clean = html.escape(ref_txt)

                f_header = Table(
                    [[
                        Paragraph(f"<b>Finding #{idx}: {cat}</b>", cell_bold),
                        Paragraph(f"Status: <b>{dec}</b>", cell_style),
                        Paragraph(f"Source: <b>{src_title}</b>", cell_style),
                    ]],
                    colWidths=[2.5 * inch, 2.0 * inch, 3.0 * inch],
                )
                f_header.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                    ("PADDING", (0, 0), (-1, -1), 3),
                ]))
                elements.append(f_header)

                # Individual paragraphs rather than nested oversized table to prevent LayoutError
                elements.append(Paragraph(f"<b>Submitted Passage:</b><br/>{sub_clean}", excerpt_style))
                elements.append(Spacer(1, 2))
                elements.append(Paragraph(f"<b>Matched Reference:</b><br/>{ref_clean}", excerpt_style))

                if note:
                    note_clean = html.escape(note)
                    elements.append(Paragraph(f"<b>Reviewer Note:</b> {note_clean}", cell_style))

                elements.append(Spacer(1, 8))
        else:
            elements.append(Paragraph("No similarity findings detected.", cell_style))

        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=6))
        elements.append(
            Paragraph(
                "<b>Audit Disclaimer:</b> This similarity report was generated by the Hybrid Multilingual Plagiarism Detection Engine. "
                "Similarity scores represent textual and semantic overlaps between digital documents and do not inherently denote academic "
                "dishonesty or copyright infringement. Authorized human reviewers should examine quoted citations, common terminology, and "
                "methodology descriptions before drawing administrative conclusions.",
                disclaimer_style,
            )
        )

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

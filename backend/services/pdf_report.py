"""
Professional engineering intelligence PDF report builder (fpdf2).

Produces a structured executive report with tables, sections, footers, and pagination.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fpdf import FPDF
from fpdf.enums import TableCellFillMode, XPos, YPos
from fpdf.fonts import FontFace

# Visual theme
COLOR_TITLE = (30, 41, 59)
COLOR_SUBTITLE = (71, 85, 105)
COLOR_HEADER_BG = (51, 65, 85)
COLOR_HEADER_TEXT = (255, 255, 255)
COLOR_ALT_ROW = (241, 245, 249)
COLOR_BODY = (30, 41, 59)
COLOR_MUTED = (100, 116, 139)

MAX_TABLE_ROWS = 15
ROW_HEIGHT = 7
HEADER_ROW_HEIGHT = 8


def _safe(text: Any, max_len: int = 80) -> str:
    if text is None:
        return ""
    s = str(text).replace("\n", " ").replace("\r", " ").strip()
    s = s.encode("latin-1", errors="replace").decode("latin-1")
    if len(s) > max_len:
        return s[: max_len - 1] + "…"
    return s


def _fmt_display(display: Optional[dict], fallback: Any = 0, suffix: str = "") -> str:
    if isinstance(display, dict) and display.get("value") is not None:
        unit = display.get("unit") or ""
        val = display["value"]
        if isinstance(val, float) and val == int(val):
            val = int(val)
        return f"{val} {unit}".strip()
    if fallback is None:
        return "—"
    if isinstance(fallback, float) and fallback == int(fallback):
        fallback = int(fallback)
    return f"{fallback}{suffix}"


@dataclass
class ReportContext:
    repo_owner: str
    repo_name: str
    generated_at: str
    total_prs: int
    filters_label: Optional[str] = None
    kpi: Dict[str, Any] = field(default_factory=dict)
    contributors: List[Dict[str, Any]] = field(default_factory=list)
    contributor_count: int = 0
    risks: List[Dict[str, Any]] = field(default_factory=list)
    stale: List[Dict[str, Any]] = field(default_factory=list)
    monthly: List[Dict[str, Any]] = field(default_factory=list)
    throughput: List[Dict[str, Any]] = field(default_factory=list)
    workflow: Dict[str, Any] = field(default_factory=dict)
    health: Dict[str, str] = field(default_factory=dict)


class EngineeringReportPDF(FPDF):
    """FPDF subclass with branded header/footer on every page."""

    def __init__(self, repo_label: str, generated_at: str):
        super().__init__()
        self._repo_label = _safe(repo_label, 60)
        self._generated_at = _safe(generated_at, 40)
        self.set_margins(14, 16, 14)
        self.set_auto_page_break(auto=True, margin=18)
        self.alias_nb_pages()

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*COLOR_MUTED)
        w = self.epw
        self.cell(w / 3, 6, self._repo_label, align="L")
        self.cell(w / 3, 6, self._generated_at, align="C")
        self.cell(w / 3, 6, f"Page {self.page_no()}/{{nb}}", align="R")
        self.set_text_color(*COLOR_BODY)


class PdfSectionRenderer:
    def __init__(self, pdf: EngineeringReportPDF):
        self.pdf = pdf

    def report_title(self, subtitle: Optional[str] = None) -> None:
        pdf = self.pdf
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*COLOR_TITLE)
        pdf.cell(0, 10, "GitHub PR Intelligence Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if subtitle:
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(*COLOR_SUBTITLE)
            pdf.cell(0, 6, _safe(subtitle), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4)

    def section(self, title: str, new_page: bool = False) -> None:
        if new_page and self.pdf.page_no() > 0:
            self.pdf.add_page()
        self.pdf.ln(3)
        self.pdf.set_font("Helvetica", "B", 13)
        self.pdf.set_text_color(*COLOR_TITLE)
        self.pdf.cell(0, 9, _safe(title, 120), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.set_draw_color(203, 213, 225)
        y = self.pdf.get_y()
        self.pdf.line(self.pdf.l_margin, y, self.pdf.w - self.pdf.r_margin, y)
        self.pdf.ln(4)

    def subsection(self, title: str) -> None:
        self.pdf.set_font("Helvetica", "B", 11)
        self.pdf.set_text_color(*COLOR_SUBTITLE)
        self.pdf.cell(0, 7, _safe(title, 100), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(2)

    def note(self, text: str) -> None:
        self.pdf.set_font("Helvetica", "I", 9)
        self.pdf.set_text_color(*COLOR_MUTED)
        self.pdf.multi_cell(
            self.pdf.epw,
            5,
            _safe(text, 200),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(2)
        self.pdf.set_text_color(*COLOR_BODY)

    def empty_banner(self, message: str) -> None:
        self.pdf.set_fill_color(254, 243, 199)
        self.pdf.set_draw_color(251, 191, 36)
        self.pdf.set_font("Helvetica", "B", 11)
        self.pdf.set_text_color(146, 64, 14)
        self.pdf.multi_cell(
            self.pdf.epw,
            8,
            _safe(message),
            border=1,
            fill=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(4)
        self.pdf.set_text_color(*COLOR_BODY)


class PdfTableRenderer:
    """Reusable fpdf2 table helper with headers, borders, and alternating rows."""

    def __init__(self, pdf: EngineeringReportPDF):
        self.pdf = pdf

    def render(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[Any]],
        col_widths: Optional[Sequence[float]] = None,
        alignments: Optional[Sequence[str]] = None,
        omitted_note: Optional[str] = None,
    ) -> None:
        if not headers:
            return

        pdf = self.pdf
        if col_widths is None:
            n = len(headers)
            col_widths = tuple(pdf.epw / n for _ in range(n))

        headings_style = FontFace(
            emphasis="BOLD",
            fill_color=COLOR_HEADER_BG,
            color=COLOR_HEADER_TEXT,
            size_pt=9,
        )

        table_rows = [
            [_safe(h, 72) for h in headers],
            *[[_safe(val, 72) for val in row] for row in rows],
        ]
        with pdf.table(
            rows=table_rows,
            col_widths=tuple(col_widths),
            line_height=ROW_HEIGHT,
            text_align=tuple(alignments) if alignments else "CENTER",
            headings_style=headings_style,
            cell_fill_mode=TableCellFillMode.EVEN_ROWS,
            cell_fill_color=COLOR_ALT_ROW,
            first_row_as_headings=True,
            width=pdf.epw,
        ):
            pass

        if omitted_note:
            pdf.ln(2)
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*COLOR_MUTED)
            pdf.cell(0, 5, _safe(omitted_note), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(*COLOR_BODY)
        pdf.ln(3)


def _compute_health_insights(
    kpi: Dict[str, Any],
    risks: List[Dict[str, Any]],
    contributors: List[Dict[str, Any]],
    total_prs: int,
) -> Dict[str, str]:
    if total_prs == 0:
        return {
            "Review Bottleneck": "N/A",
            "PR Risk": "N/A",
            "Contributor Load": "N/A",
            "Merge Efficiency": "N/A",
        }

    wait_days = float(kpi.get("avg_wait_for_review") or 0)
    if wait_days > 3:
        bottleneck = "High"
    elif wait_days > 1:
        bottleneck = "Moderate"
    else:
        bottleneck = "Low"

    if risks:
        avg_risk = sum(float(r.get("risk_score") or 0) for r in risks) / len(risks)
        if avg_risk >= 60:
            pr_risk = "High"
        elif avg_risk >= 35:
            pr_risk = "Medium"
        else:
            pr_risk = "Low"
    else:
        pr_risk = "Low"

    totals = [int(c.get("total_prs") or 0) for c in contributors]
    if totals and sum(totals) > 0:
        max_share = max(totals) / sum(totals) * 100
        if max_share > 50:
            load = "Concentrated"
        elif max_share > 30:
            load = "Moderate"
        else:
            load = "Balanced"
    else:
        load = "N/A"

    merge_rate = float(kpi.get("merge_rate") or 0)
    if merge_rate >= 70:
        efficiency = "Good"
    elif merge_rate >= 40:
        efficiency = "Moderate"
    else:
        efficiency = "Needs attention"

    return {
        "Review Bottleneck": bottleneck,
        "PR Risk": pr_risk,
        "Contributor Load": load,
        "Merge Efficiency": efficiency,
    }


def _compute_workflow_insights(
    prs: List[Any],
    risks: List[Dict[str, Any]],
    contributors: List[Dict[str, Any]],
) -> Dict[str, Any]:
    open_prs = [p for p in prs if p.state == "OPEN"]
    no_review = sum(1 for p in open_prs if (p.review_count or 0) == 0)
    high_risk = sum(1 for r in risks if float(r.get("risk_score") or 0) >= 50)
    blocked = sum(
        1
        for r in risks
        if float(r.get("bottleneck_probability") or 0) >= 50
    )

    wait_avgs = [
        float(c.get("avg_wait_for_review") or 0) * 24
        for c in contributors
        if c.get("avg_wait_for_review") is not None
    ]
    fastest_h = min(wait_avgs) if wait_avgs else 0
    slowest_h = max(wait_avgs) if wait_avgs else 0

    return {
        "prs_without_reviews": no_review,
        "high_risk_prs": high_risk,
        "blocked_prs": blocked,
        "fastest_reviewer_avg_hrs": round(fastest_h, 1),
        "slowest_review_queue": _format_hours_as_days(slowest_h),
    }


def _format_hours_as_days(hours: float) -> str:
    if hours <= 0:
        return "0 hrs"
    if hours < 24:
        return f"{hours:.1f} hrs"
    return f"{hours / 24:.1f} days"


def _kpi_summary_rows(ctx: ReportContext) -> List[Tuple[str, str]]:
    k = ctx.kpi
    return [
        ("Total PRs", str(ctx.total_prs)),
        ("Open PRs", str(k.get("open_prs", 0))),
        ("Merge Rate", f"{k.get('merge_rate', 0)}%"),
        (
            "Avg Review Time",
            _fmt_display(k.get("avg_review_duration_display"), k.get("avg_review_duration")),
        ),
        (
            "Avg Cycle Time",
            _fmt_display(k.get("avg_cycle_time_display"), k.get("avg_cycle_time")),
        ),
        ("Contributors", str(ctx.contributor_count)),
        ("Stale PRs", str(k.get("stale_prs", 0))),
    ]


def _stale_row(s: Dict[str, Any]) -> Tuple[str, str, str, str]:
    reasons = s.get("reasons") or []
    actions = s.get("recommended_actions") or []
    reason = reasons[0] if reasons else "Needs attention"
    action = actions[0] if actions else "Review PR"
    age = s.get("age_days", 0)
    age_s = f"{age}d" if age else "0d"
    return (
        f"#{s.get('number', '')}",
        age_s,
        _safe(reason, 40),
        _safe(action, 45),
    )


def build_engineering_report_pdf(ctx: ReportContext) -> bytes:
    """Render the full multi-section engineering report."""
    repo_label = f"{ctx.repo_owner}/{ctx.repo_name}"
    pdf = EngineeringReportPDF(repo_label, ctx.generated_at)
    sections = PdfSectionRenderer(pdf)
    tables = PdfTableRenderer(pdf)

    # —— Page 1: Executive Summary ——
    pdf.add_page()
    sections.report_title("Engineering Analytics Report")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_SUBTITLE)
    meta = [
        f"Repository: {repo_label}",
        f"Generated (UTC): {ctx.generated_at}",
        f"Total pull requests analyzed: {ctx.total_prs}",
    ]
    if ctx.filters_label:
        meta.append(f"Filters: {ctx.filters_label}")
    for line in meta:
        pdf.cell(0, 5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    if ctx.total_prs == 0:
        sections.empty_banner("No Pull Request Analytics Available")
        tables.render(
            ["Metric", "Value"],
            [("Total PRs", "0"), ("Open PRs", "0"), ("Contributors", "0")],
            col_widths=(pdf.epw * 0.55, pdf.epw * 0.45),
            alignments=("LEFT", "RIGHT"),
        )
        out = pdf.output()
        return bytes(out) if isinstance(out, (bytes, bytearray)) else str(out).encode("latin-1")

    sections.section("Executive Summary")
    sections.subsection("KPI Summary")
    tables.render(
        ["Metric", "Value"],
        _kpi_summary_rows(ctx),
        col_widths=(pdf.epw * 0.55, pdf.epw * 0.45),
        alignments=("LEFT", "RIGHT"),
    )

    sections.subsection("Repository Health Summary")
    health_rows = [(k, v) for k, v in ctx.health.items()]
    tables.render(
        ["Insight", "Status"],
        health_rows,
        col_widths=(pdf.epw * 0.55, pdf.epw * 0.45),
        alignments=("LEFT", "CENTER"),
    )

    # —— Page 2: Contributors ——
    sections.section("Contributor Analytics", new_page=True)
    contrib_rows = []
    shown = ctx.contributors[:MAX_TABLE_ROWS]
    for c in shown:
        total = int(c.get("total_prs") or 0)
        merged = int(c.get("merged_prs") or 0)
        open_p = int(c.get("open_prs") or total - merged)
        contrib_rows.append(
            (
                _safe(c.get("username"), 28),
                str(total),
                str(open_p),
                str(merged),
                f"{c.get('merge_rate', 0)}%",
            )
        )
    omitted = None
    extra = ctx.contributor_count - len(shown)
    if extra > 0:
        omitted = f"+ {extra} more contributor(s) omitted"
    if contrib_rows:
        tables.render(
            ["Contributor", "Total PRs", "Open", "Merged", "Merge %"],
            contrib_rows,
            col_widths=(
                pdf.epw * 0.28,
                pdf.epw * 0.18,
                pdf.epw * 0.14,
                pdf.epw * 0.14,
                pdf.epw * 0.18,
            ),
            alignments=("LEFT", "CENTER", "CENTER", "CENTER", "CENTER"),
            omitted_note=omitted,
        )
    else:
        sections.note("No contributor activity recorded.")

    # —— Page 3: High Risk PRs ——
    sections.section("High Risk Pull Requests", new_page=True)
    risk_rows = []
    sorted_risks = sorted(
        ctx.risks,
        key=lambda r: float(r.get("risk_score") or 0),
        reverse=True,
    )[:MAX_TABLE_ROWS]
    for r in sorted_risks:
        delay = r.get("predicted_delay_days")
        delay_s = f"{delay}d" if delay is not None else "—"
        risk_rows.append(
            (
                f"#{r.get('number', '')}",
                f"{r.get('risk_score', 0)}%",
                f"{r.get('bottleneck_probability', 0)}%",
                delay_s,
                _safe(r.get("author"), 24),
            )
        )
    risk_omitted = None
    if len(ctx.risks) > len(sorted_risks):
        risk_omitted = f"+ {len(ctx.risks) - len(sorted_risks)} more open PR(s) omitted"
    if risk_rows:
        tables.render(
            ["PR", "Risk", "Bottleneck", "Delay", "Author"],
            risk_rows,
            col_widths=(
                pdf.epw * 0.12,
                pdf.epw * 0.14,
                pdf.epw * 0.18,
                pdf.epw * 0.14,
                pdf.epw * 0.32,
            ),
            alignments=("CENTER", "CENTER", "CENTER", "CENTER", "LEFT"),
            omitted_note=risk_omitted,
        )
    else:
        sections.note("No open pull requests with risk scores.")

    # —— Page 4: Stale PRs ——
    sections.section("Stale PR Analysis", new_page=True)
    stale_sorted = sorted(
        ctx.stale,
        key=lambda s: (
            {"high": 0, "medium": 1, "low": 2}.get(s.get("severity", "low"), 3),
            -int(s.get("age_days") or 0),
        ),
    )
    stale_shown = stale_sorted[:MAX_TABLE_ROWS]
    stale_rows = [_stale_row(s) for s in stale_shown]
    stale_omitted = None
    if len(ctx.stale) > len(stale_shown):
        stale_omitted = f"+ {len(ctx.stale) - len(stale_shown)} remaining stale PR(s) omitted"
    if stale_rows:
        tables.render(
            ["PR", "Age", "Reason", "Suggested Action"],
            stale_rows,
            col_widths=(
                pdf.epw * 0.10,
                pdf.epw * 0.10,
                pdf.epw * 0.38,
                pdf.epw * 0.42,
            ),
            alignments=("CENTER", "CENTER", "LEFT", "LEFT"),
            omitted_note=stale_omitted,
        )
    else:
        sections.note("No stale pull requests detected for the current threshold.")

    # —— Page 5: Workflow Insights ——
    sections.section("Workflow Insights", new_page=True)
    w = ctx.workflow
    workflow_rows = [
        ("PRs without reviews", str(w.get("prs_without_reviews", 0))),
        ("High Risk PRs", str(w.get("high_risk_prs", 0))),
        ("Blocked PRs (bottleneck ≥50%)", str(w.get("blocked_prs", 0))),
        ("Fastest Reviewer Avg", f"{w.get('fastest_reviewer_avg_hrs', 0)} hrs"),
        ("Slowest Review Queue", str(w.get("slowest_review_queue", "—"))),
    ]
    tables.render(
        ["Insight", "Count / Value"],
        workflow_rows,
        col_widths=(pdf.epw * 0.55, pdf.epw * 0.45),
        alignments=("LEFT", "RIGHT"),
    )

    # —— Page 6: Trends ——
    sections.section("Trend Analytics", new_page=True)
    sections.subsection("Monthly PR Flow (last 6 months)")
    monthly_rows = [
        (
            _safe(m.get("month")),
            str(m.get("created", 0)),
            str(m.get("merged", 0)),
            str(m.get("closed", 0)),
        )
        for m in ctx.monthly
    ]
    if monthly_rows:
        tables.render(
            ["Month", "Created", "Merged", "Closed"],
            monthly_rows,
            col_widths=(pdf.epw * 0.34, pdf.epw * 0.22, pdf.epw * 0.22, pdf.epw * 0.22),
        )
    else:
        sections.note("No monthly activity in the selected period.")

    sections.subsection("Weekly Throughput (merged PRs)")
    throughput_rows = [
        (_safe(t.get("week")), str(t.get("prs", 0))) for t in ctx.throughput
    ]
    if throughput_rows:
        total_merged = sum(int(t.get("prs", 0)) for t in ctx.throughput)
        avg_weekly = round(total_merged / max(len(ctx.throughput), 1), 1)
        tables.render(
            ["Week", "Merged PRs"],
            throughput_rows,
            col_widths=(pdf.epw * 0.55, pdf.epw * 0.45),
            alignments=("LEFT", "CENTER"),
        )
        sections.note(
            f"Merge trend summary: {total_merged} PRs merged over {len(ctx.throughput)} weeks "
            f"(avg {avg_weekly} per week)."
        )
    else:
        sections.note("No merged PRs in the weekly throughput window.")

    out = pdf.output()
    return bytes(out) if isinstance(out, (bytes, bytearray)) else str(out).encode("latin-1")

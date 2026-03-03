import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, Image,
)
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from report.styles import (
    get_styles, ParagraphStyle, PRIMARY, SECONDARY, ACCENT, WARNING, DANGER,
    LIGHT_BG, LIGHT, WHITE, TEXT_PRIMARY, TEXT_SECONDARY, BORDER, CARD_BG,
    SCORE_HIGH, SCORE_MEDIUM, SCORE_LOW, get_score_color, SOURCE_COLORS,
    DARK_BG, DARK_CARD, DARK_BORDER, DARK_TEXT, DARK_TEXT_MUTED, DARK_TABLE_ALT,
)
from report.charts import (
    create_visibility_bar_chart, create_source_pie_chart,
    create_mini_score_box,
)
from models.data_models import (
    GEOReport, PromptCategory, LLMProvider, SourceCategory,
)


# ── Constants ──────────────────────────────────────────────

_LOGO_COVER_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "jolly_logo_cover.png")
_LOGO_PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "jolly_logo_pdf.png")
_PAGE_WIDTH, _PAGE_HEIGHT = A4
_CONTENT_WIDTH = _PAGE_WIDTH - 1.4 * inch  # accounting for margins


def _get_logo_path(variant="cover"):
    """Return the absolute path to a Jolly logo PNG, or None if not found."""
    path = _LOGO_COVER_PATH if variant == "cover" else _LOGO_PDF_PATH
    path = os.path.abspath(path)
    return path if os.path.exists(path) else None


def _section_header(title: str, styles) -> list:
    """Reusable section header with title and accent underline."""
    return [
        Spacer(1, 16),
        Paragraph(title, styles["SectionTitle"]),
        HRFlowable(width="100%", thickness=2, color=SECONDARY,
                    spaceBefore=2, spaceAfter=18),
    ]


# ── Main Entry Point ──────────────────────────────────────

def generate_pdf(report: GEOReport, output_dir: str = "outputs") -> str:
    """Generate the full PDF report and return the file path."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = report.brand_input.brand_name.replace(" ", "_").replace("/", "_")
    filename = f"GEO_Report_{safe_name}_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)

    try:
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            topMargin=0.7 * inch,
            bottomMargin=0.65 * inch,
            leftMargin=0.7 * inch,
            rightMargin=0.7 * inch,
        )

        styles = get_styles()
        elements = []

        # 1. Cover page
        elements.extend(_build_cover_page(report, styles))
        elements.append(PageBreak())

        # 2. Table of Contents
        elements.extend(_build_table_of_contents(report, styles))
        elements.append(PageBreak())

        # 3. Executive summary
        elements.extend(_build_executive_summary(report, styles))
        elements.append(PageBreak())

        # 4. Per-prompt detailed results
        elements.extend(_build_prompt_details(report, styles))

        # 5. Source analysis
        elements.extend(_build_source_analysis(report, styles))
        elements.append(PageBreak())

        # 6. Competitor comparison
        elements.extend(_build_competitor_comparison(report, styles))
        elements.append(PageBreak())

        # 7. Weak points & strategy
        elements.extend(_build_strategy_section(report, styles))

        # 8. Appendix: All sources
        elements.extend(_build_source_appendix(report, styles))

        doc.build(elements, onFirstPage=_draw_page_bg, onLaterPages=_draw_page_bg_with_footer)
        return filepath

    except Exception as e:
        logger.error("PDF generation failed: %s", e, exc_info=True)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        raise RuntimeError(f"PDF generation failed: {e}") from e


# ── Page Background & Footers ─────────────────────────────

def _draw_page_bg(canvas, doc):
    """Dark background for the cover page (no footer)."""
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, _PAGE_WIDTH, _PAGE_HEIGHT, fill=True, stroke=False)
    canvas.restoreState()


def _draw_page_bg_with_footer(canvas, doc):
    """Dark background + footer for content pages."""
    canvas.saveState()

    # Dark background
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, _PAGE_WIDTH, _PAGE_HEIGHT, fill=True, stroke=False)

    # Footer
    page_w = doc.pagesize[0]
    margin = 0.7 * inch

    # Thin accent line
    canvas.setStrokeColor(SECONDARY)
    canvas.setLineWidth(0.75)
    canvas.line(margin, 0.5 * inch, page_w - margin, 0.5 * inch)

    # Left: branding
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(DARK_TEXT_MUTED)
    canvas.drawString(margin, 0.32 * inch, "GEO Visibility Report  \u2022  Powered by Jolly SEO")

    # Right: page number
    page_num = canvas.getPageNumber()
    canvas.drawRightString(page_w - margin, 0.32 * inch, f"Page {page_num}")

    canvas.restoreState()


# ── 1. Cover Page ─────────────────────────────────────────

def _build_cover_page(report: GEOReport, styles) -> list:
    elements = []

    # Push down from top
    elements.append(Spacer(1, 0.5 * inch))

    # Jolly logo (light text on dark bg)
    logo_path = _get_logo_path("cover")
    if logo_path:
        logo = Image(logo_path, width=2.4 * inch, height=1.2 * inch)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 0.3 * inch))

    # Accent bar
    accent_bar = Table([[""]], colWidths=[_CONTENT_WIDTH], rowHeights=[4])
    accent_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SECONDARY),
    ]))
    elements.append(accent_bar)

    elements.append(Spacer(1, 0.15 * inch))

    # Main cover block
    cover_data = [
        [Spacer(1, 14)],
        [Paragraph("GEO VISIBILITY REPORT", styles["CoverTitle"])],
        [Spacer(1, 10)],
        [Paragraph(report.brand_input.brand_name, styles["CoverSubtitle"])],
        [Spacer(1, 24)],
        [Paragraph(f"Generated: {report.generated_at}", styles["CoverDate"])],
        [Paragraph(f"Website: {report.brand_input.website_url}", styles["CoverDate"])],
        [Spacer(1, 14)],
    ]

    cover_table = Table(cover_data, colWidths=[_CONTENT_WIDTH])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 28),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 28),
        ("LEFTPADDING", (0, 0), (-1, -1), 32),
        ("RIGHTPADDING", (0, 0), (-1, -1), 32),
        ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
    ]))
    elements.append(cover_table)

    elements.append(Spacer(1, 0.35 * inch))

    # Stats row
    total_prompts = sum(len(v) for v in report.brand_input.prompts.values())
    valid_responses = sum(1 for r in report.responses if r.error is None)
    num_sources = len(report.all_sources)

    stats = [
        (str(total_prompts), "Discovery Prompts"),
        (str(valid_responses), "LLM Responses"),
        (str(num_sources), "Sources Mapped"),
    ]
    stats_data = [[
        Paragraph(
            f'<font size="18"><b>{val}</b></font><br/>'
            f'<font size="7" color="{DARK_TEXT_MUTED.hexval()}">{label}</font>',
            ParagraphStyle("CoverStat", alignment=TA_CENTER, leading=22,
                           textColor=DARK_TEXT, fontName="Helvetica")
        ) for val, label in stats
    ]]

    col_w = _CONTENT_WIDTH / 3
    stats_table = Table(stats_data, colWidths=[col_w] * 3)
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
        ("LINEBEFORE", (1, 0), (1, 0), 0.5, DARK_BORDER),
        ("LINEBEFORE", (2, 0), (2, 0), 0.5, DARK_BORDER),
    ]))
    elements.append(stats_table)

    elements.append(Spacer(1, 0.25 * inch))

    # Competitors
    if report.brand_input.competitors:
        comp_text = (
            f'<font color="{DARK_TEXT_MUTED.hexval()}">Competitors Analyzed:</font>  '
            + ", ".join(f"<b>{c}</b>" for c in report.brand_input.competitors)
        )
        p = Paragraph(comp_text, ParagraphStyle(
            "CoverComp", parent=styles["BodyText2"], alignment=TA_CENTER))
        elements.append(p)

    elements.append(Spacer(1, 0.3 * inch))

    # Footer tagline
    elements.append(Paragraph(
        f'Powered by <font color="{SECONDARY.hexval()}"><b>Jolly SEO</b></font>  '
        f'\u2022  Generative Engine Optimization',
        ParagraphStyle("CoverTagline", parent=styles["SmallText"], alignment=TA_CENTER)
    ))

    return elements


# ── 2. Table of Contents ─────────────────────────────────

def _build_table_of_contents(report: GEOReport, styles) -> list:
    elements = []

    elements.extend(_section_header("Contents", styles))

    # Report description
    elements.append(Paragraph(
        "This GEO Visibility Report evaluates how prominently your brand appears "
        "in AI-generated responses across major large language models. It measures "
        "brand mentions, citations, source attribution, and competitive positioning "
        "to help you understand and improve your Generative Engine Optimization (GEO) "
        "performance.",
        styles["ReportIntro"]
    ))

    elements.append(Spacer(1, 8))

    toc_style = ParagraphStyle(
        "TOCEntry", parent=styles["BodyText2"],
        fontSize=11, leading=20, spaceBefore=4, spaceAfter=4,
    )
    toc_num_style = ParagraphStyle(
        "TOCNum", parent=toc_style, alignment=TA_LEFT,
        textColor=SECONDARY, fontName="Helvetica-Bold",
    )

    sections = [
        ("01", "Executive Summary",
         "Overall visibility score, provider and category breakdown, key findings"),
        ("02", "Prompt-by-Prompt Results",
         "Detailed analysis of each discovery prompt across all LLM providers"),
        ("03", "Source Analysis",
         "Distribution of cited sources by type and most frequently referenced domains"),
        ("04", "Competitor Comparison",
         "Visibility scores and prompt-level heatmap comparing brand to competitors"),
        ("05", "Strategy Recommendations",
         "Identified weak points and prioritized action plan"),
        ("06", "Source Appendix",
         "Complete list of all sources referenced in LLM responses"),
    ]

    for num, title, desc in sections:
        row_data = [[
            Paragraph(num, toc_num_style),
            Paragraph(
                f'<b>{title}</b><br/>'
                f'<font size="8" color="{DARK_TEXT_MUTED.hexval()}">{desc}</font>',
                toc_style
            ),
        ]]
        row_table = Table(row_data, colWidths=[0.45 * inch, _CONTENT_WIDTH - 0.55 * inch])
        row_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, DARK_BORDER),
        ]))
        elements.append(row_table)

    elements.append(Spacer(1, 0.35 * inch))

    # Report scope summary
    total_prompts = sum(len(v) for v in report.brand_input.prompts.values())
    valid_responses = sum(1 for r in report.responses if r.error is None)
    provider_count = len(set(r.provider.value for r in report.responses if r.error is None))

    scope_text = (
        f'This report analyzes <b>{report.brand_input.brand_name}</b> '
        f'across <b>{provider_count}</b> AI platforms using '
        f'<b>{total_prompts}</b> discovery prompts, generating '
        f'<b>{valid_responses}</b> responses and mapping '
        f'<b>{len(report.all_sources)}</b> unique sources.'
    )
    scope_box = Table(
        [[Paragraph(scope_text, ParagraphStyle(
            "ScopeText", parent=styles["BodyText2"],
            fontSize=10, leading=16, textColor=DARK_TEXT))]],
        colWidths=[_CONTENT_WIDTH],
    )
    scope_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
        ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    elements.append(scope_box)

    elements.append(Spacer(1, 0.2 * inch))

    # Report outputs summary
    outputs_text = (
        '<b>This report outputs:</b> an overall visibility score, per-provider '
        'and per-category breakdowns, prompt-level response analysis, source '
        'mapping, competitor benchmarking, and prioritized strategy recommendations.'
    )
    elements.append(Paragraph(outputs_text, ParagraphStyle(
        "OutputsText", parent=styles["ReportIntro"], fontSize=10, leading=15)))

    return elements


# ── 3. Executive Summary ─────────────────────────────────

def _build_executive_summary(report: GEOReport, styles) -> list:
    elements = []

    elements.extend(_section_header("Executive Summary", styles))

    vis = report.brand_visibility
    if not vis:
        elements.append(Paragraph("No visibility data available.", styles["BodyText2"]))
        return elements

    # Overall score card
    score_pct = f"{vis.overall_score:.0%}"
    score_color = get_score_color(vis.overall_score)
    score_label = (
        "STRONG" if vis.overall_score >= 0.6
        else "MODERATE" if vis.overall_score >= 0.3
        else "NEEDS IMPROVEMENT"
    )

    score_data = [[
        Paragraph(
            f'<font size="42" color="{score_color.hexval()}">{score_pct}</font>',
            ParagraphStyle("ScoreBig", alignment=TA_CENTER,
                           fontName="Helvetica-Bold", leading=50)
        ),
    ], [
        Paragraph(
            f'<font size="11">Overall Brand Visibility</font><br/>'
            f'<font size="9" color="{score_color.hexval()}">{score_label}</font>',
            ParagraphStyle("ScoreLabel", alignment=TA_CENTER, fontSize=11,
                           textColor=DARK_TEXT_MUTED, fontName="Helvetica", leading=16)
        ),
    ]]

    score_table = Table(score_data, colWidths=[_CONTENT_WIDTH])
    score_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
        ("TOPPADDING", (0, 0), (0, 0), 24),
        ("BOTTOMPADDING", (0, -1), (0, -1), 18),
        ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 20))

    # Provider scores bar chart
    if vis.by_provider:
        chart = create_visibility_bar_chart(vis.by_provider, title="Visibility by LLM Provider")
        elements.append(chart)
        elements.append(Spacer(1, 16))

    # Category scores bar chart
    if vis.by_category:
        chart = create_visibility_bar_chart(vis.by_category, title="Visibility by Intent Category")
        elements.append(chart)
        elements.append(Spacer(1, 24))

    # Key findings
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Key Findings", styles["SubsectionTitle"]))
    elements.append(Spacer(1, 6))
    findings = _generate_key_findings(report)
    for finding in findings[:5]:
        elements.append(Paragraph(f"\u2022  {finding}", styles["BulletItem"]))
    elements.append(Spacer(1, 20))

    # Top recommendations preview
    if report.strategy_recommendations:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Priority Recommendations", styles["SubsectionTitle"]))
        elements.append(Spacer(1, 6))
        for rec in report.strategy_recommendations[:3]:
            p_color = {"high": DANGER, "medium": WARNING, "low": SCORE_HIGH}.get(
                rec.priority, DARK_TEXT)
            rationale_trunc = rec.rationale[:100] + "..." if len(rec.rationale) > 100 else rec.rationale
            elements.append(Paragraph(
                f'<font color="{p_color.hexval()}">\u25cf {rec.priority.upper()}</font>  '
                f'<b>{rec.service}</b> \u2014 {rationale_trunc}',
                styles["BulletItem"]
            ))

    return elements


# ── 4. Per-Prompt Details ─────────────────────────────────

def _build_prompt_details(report: GEOReport, styles) -> list:
    elements = []

    elements.extend(_section_header("Prompt-by-Prompt Results", styles))

    prompt_index = 0
    for category in PromptCategory:
        prompts = report.brand_input.prompts.get(category, [])
        for prompt_text in prompts:
            prompt_index += 1

            prompt_responses = [
                r for r in report.responses
                if r.prompt == prompt_text and r.error is None
            ]

            section = []

            # Prompt header with number badge
            section.append(Paragraph(
                f'<font color="{SECONDARY.hexval()}">Prompt {prompt_index}</font>'
                f'  \u2022  {category.value}',
                styles["SubsectionTitle"]
            ))
            section.append(Paragraph(
                f'\u201c{prompt_text}\u201d',
                styles["PromptText"]
            ))
            section.append(Spacer(1, 8))

            # LLM results table
            if prompt_responses:
                table_data = [[
                    Paragraph("LLM Provider", styles["TableHeader"]),
                    Paragraph("Mentioned", styles["TableHeader"]),
                    Paragraph("Cited", styles["TableHeader"]),
                    Paragraph("Competitors Found", styles["TableHeader"]),
                    Paragraph("Sources", styles["TableHeader"]),
                ]]

                for r in prompt_responses:
                    m_icon = "\u2713" if r.brand_mentioned else "\u2717"
                    m_color = SCORE_HIGH if r.brand_mentioned else SCORE_LOW
                    c_icon = "\u2713" if r.brand_cited else "\u2717"
                    c_color = SCORE_HIGH if r.brand_cited else SCORE_LOW

                    comp_list = [c for c, m in r.competitor_mentions.items() if m]
                    comp_text = ", ".join(comp_list) if comp_list else "\u2014"

                    table_data.append([
                        Paragraph(r.provider.value, styles["TableCell"]),
                        Paragraph(
                            f'<font color="{m_color.hexval()}"><b>{m_icon}</b></font>',
                            ParagraphStyle("CellCenter", parent=styles["TableCell"],
                                           alignment=TA_CENTER)),
                        Paragraph(
                            f'<font color="{c_color.hexval()}"><b>{c_icon}</b></font>',
                            ParagraphStyle("CellCenter2", parent=styles["TableCell"],
                                           alignment=TA_CENTER)),
                        Paragraph(comp_text, styles["TableCell"]),
                        Paragraph(str(len(r.sources)),
                                  ParagraphStyle("CellCenter3", parent=styles["TableCell"],
                                                 alignment=TA_CENTER)),
                    ])

                col_widths = [1.5 * inch, 0.75 * inch, 0.65 * inch, 2.0 * inch, 0.65 * inch]
                t = Table(table_data, colWidths=col_widths)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (1, 0), (2, -1), "CENTER"),
                    ("ALIGN", (4, 0), (4, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, DARK_BORDER),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [DARK_CARD, DARK_TABLE_ALT]),
                ]))
                section.append(t)
                section.append(Spacer(1, 12))

            # Sources for this prompt
            prompt_sources = []
            for r in prompt_responses:
                prompt_sources.extend(r.sources)

            if prompt_sources:
                seen = set()
                unique_sources = []
                for s in prompt_sources:
                    if s.url not in seen:
                        seen.add(s.url)
                        unique_sources.append(s)

                section.append(Spacer(1, 4))
                section.append(Paragraph(
                    f"Sources Referenced ({len(unique_sources)})",
                    ParagraphStyle("SourceHdr", parent=styles["TableCell"],
                                   fontName="Helvetica-Bold", fontSize=9,
                                   spaceBefore=4, spaceAfter=6)
                ))

                source_data = [[
                    Paragraph("#", styles["TableHeader"]),
                    Paragraph("Source", styles["TableHeader"]),
                    Paragraph("Type", styles["TableHeader"]),
                ]]

                for idx, src in enumerate(unique_sources[:12], 1):
                    url_display = src.url[:60] + "..." if len(src.url) > 60 else src.url
                    title_text = f"{src.title}<br/>" if src.title else ""
                    source_data.append([
                        Paragraph(str(idx), styles["TableCell"]),
                        Paragraph(
                            f'{title_text}<font color="{SECONDARY.hexval()}">{url_display}</font>',
                            styles["SourceURL"]),
                        Paragraph(src.category.value, styles["TableCell"]),
                    ])

                st = Table(source_data, colWidths=[0.3 * inch, 4.0 * inch, 1.25 * inch])
                st.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.3, DARK_BORDER),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [DARK_CARD, DARK_TABLE_ALT]),
                ]))
                section.append(st)

            section.append(Spacer(1, 28))
            elements.extend(section)

            if prompt_index % 2 == 0:
                elements.append(PageBreak())

    return elements


# ── 5. Source Analysis ────────────────────────────────────

def _build_source_analysis(report: GEOReport, styles) -> list:
    elements = []

    elements.extend(_section_header("Source Analysis", styles))

    elements.append(Paragraph(
        f"Total unique sources found across all LLM responses: "
        f"<b>{len(report.all_sources)}</b>",
        styles["BodyText2"]
    ))
    elements.append(Spacer(1, 18))

    # Source distribution pie chart
    if report.source_counts_by_category:
        elements.append(Paragraph("Source Distribution by Type", styles["SubsectionTitle"]))
        elements.append(Spacer(1, 6))
        chart = create_source_pie_chart(report.source_counts_by_category)
        elements.append(chart)
        elements.append(Spacer(1, 24))

    # Top domains table
    from analysis.source_parser import get_top_domains
    top_domains = get_top_domains(report.all_sources, top_n=15)

    if top_domains:
        elements.append(Paragraph("Most Frequently Cited Domains", styles["SubsectionTitle"]))
        elements.append(Spacer(1, 8))

        domain_data = [[
            Paragraph("Rank", styles["TableHeader"]),
            Paragraph("Domain", styles["TableHeader"]),
            Paragraph("Citations", styles["TableHeader"]),
        ]]

        for rank, (domain, count) in enumerate(top_domains, 1):
            domain_data.append([
                Paragraph(str(rank), styles["TableCell"]),
                Paragraph(domain, styles["TableCell"]),
                Paragraph(str(count),
                          ParagraphStyle("DomainCount", parent=styles["TableCell"],
                                         alignment=TA_CENTER, fontName="Helvetica-Bold")),
            ])

        dt = Table(domain_data, colWidths=[0.6 * inch, 3.5 * inch, 0.9 * inch])
        dt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, DARK_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [DARK_CARD, DARK_TABLE_ALT]),
        ]))
        elements.append(dt)

    return elements


# ── 6. Competitor Comparison ─────────────────────────────

def _build_competitor_comparison(report: GEOReport, styles) -> list:
    elements = []

    elements.extend(_section_header("Competitor Comparison", styles))

    # Overall scores comparison
    all_entities = {}
    if report.brand_visibility:
        all_entities[report.brand_input.brand_name] = report.brand_visibility.overall_score
    for comp_name, comp_vis in report.competitor_visibility.items():
        all_entities[comp_name] = comp_vis.overall_score

    if all_entities:
        elements.append(Paragraph("Overall Visibility Scores", styles["SubsectionTitle"]))
        elements.append(Spacer(1, 6))
        chart = create_visibility_bar_chart(all_entities, title="")
        elements.append(chart)
        elements.append(Spacer(1, 28))

    # Heatmap
    all_prompts = []
    for cat in PromptCategory:
        all_prompts.extend(report.brand_input.prompts.get(cat, []))

    if all_prompts and all_entities:
        elements.append(Paragraph("Prompt-Level Visibility Heatmap", styles["SubsectionTitle"]))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(
            '<font color="#22C55E">\u25cf</font> = Mentioned  '
            '<font color="#E63600">\u25cf</font> = Not mentioned  '
            '\u2014  Shows brand presence in LLM responses per prompt.',
            styles["SmallText"]
        ))
        elements.append(Spacer(1, 10))

        prompt_labels = [f"P{i+1}" for i in range(len(all_prompts))]

        header = [Paragraph("Brand / Competitor", styles["TableHeader"])]
        for pl in prompt_labels:
            header.append(Paragraph(pl, styles["TableHeader"]))

        heatmap_data = [header]

        # Brand row
        brand_row = [Paragraph(f"<b>{report.brand_input.brand_name}</b>", styles["TableCell"])]
        for prompt in all_prompts:
            score = report.brand_visibility.by_prompt.get(prompt, 0) if report.brand_visibility else 0
            color = SCORE_HIGH if score > 0.5 else SCORE_LOW
            icon = "\u2713" if score > 0.5 else "\u2717"
            brand_row.append(Paragraph(
                f'<font color="{color.hexval()}"><b>{icon}</b></font>',
                ParagraphStyle("HC", alignment=TA_CENTER, fontSize=8,
                               fontName="Helvetica-Bold", textColor=DARK_TEXT)
            ))
        heatmap_data.append(brand_row)

        for comp_name, comp_vis in report.competitor_visibility.items():
            row = [Paragraph(comp_name, styles["TableCell"])]
            for prompt in all_prompts:
                score = comp_vis.by_prompt.get(prompt, 0)
                color = SCORE_HIGH if score > 0.5 else SCORE_LOW
                icon = "\u2713" if score > 0.5 else "\u2717"
                row.append(Paragraph(
                    f'<font color="{color.hexval()}"><b>{icon}</b></font>',
                    ParagraphStyle("HC2", alignment=TA_CENTER, fontSize=8,
                                   fontName="Helvetica-Bold", textColor=DARK_TEXT)
                ))
            heatmap_data.append(row)

        entity_col = 1.6 * inch
        prompt_col = (_CONTENT_WIDTH - entity_col) / max(len(prompt_labels), 1)
        col_widths = [entity_col] + [prompt_col] * len(prompt_labels)

        ht = Table(heatmap_data, colWidths=col_widths)
        ht.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, DARK_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [DARK_CARD, DARK_TABLE_ALT]),
        ]))
        elements.append(ht)

        # Prompt legend
        elements.append(Spacer(1, 14))
        elements.append(Paragraph("Prompt Key:", ParagraphStyle(
            "PromptKey", fontName="Helvetica-Bold", fontSize=8,
            textColor=DARK_TEXT, spaceBefore=4, spaceAfter=6,
        )))
        for i, prompt in enumerate(all_prompts):
            elements.append(Paragraph(
                f'<font color="{SECONDARY.hexval()}">P{i+1}</font>: '
                f'{prompt[:80]}{"..." if len(prompt) > 80 else ""}',
                styles["SmallText"]
            ))

    return elements


# ── 7. Strategy Section ──────────────────────────────────

def _build_strategy_section(report: GEOReport, styles) -> list:
    elements = []

    elements.extend(_section_header("Weak Points & Strategy Recommendations", styles))

    # Weak points
    if report.weak_points:
        elements.append(Paragraph("Identified Weak Points", styles["SubsectionTitle"]))
        elements.append(Spacer(1, 8))

        for i, wp in enumerate(report.weak_points, 1):
            wp_data = [[
                Paragraph(
                    f'<font color="{SECONDARY.hexval()}"><b>#{i}</b></font>  {wp.description}',
                    styles["BodyText2"]),
            ]]
            if wp.prompt and not wp.prompt.startswith("["):
                wp_data.append([
                    Paragraph(f'<i>Prompt: \u201c{wp.prompt[:75]}...\u201d</i>',
                              styles["SmallText"])
                ])
            if wp.dominating_competitors:
                wp_data.append([
                    Paragraph(
                        f"Dominating competitors: <b>{', '.join(wp.dominating_competitors)}</b>",
                        styles["SmallText"])
                ])
            wp_data.append([
                Paragraph(
                    f'<font color="{SECONDARY.hexval()}">'
                    f'Recommended: {wp.recommended_service}</font>',
                    styles["SmallText"])
            ])

            wp_table = Table(wp_data, colWidths=[_CONTENT_WIDTH - 0.2 * inch])
            wp_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
                ("LINEABOVE", (0, 0), (-1, 0), 2, SECONDARY),
            ]))
            elements.append(wp_table)
            elements.append(Spacer(1, 14))

    elements.append(Spacer(1, 18))

    # Strategy recommendations
    if report.strategy_recommendations:
        elements.append(Paragraph("Strategic Recommendations", styles["SubsectionTitle"]))
        elements.append(Spacer(1, 8))

        for rec in report.strategy_recommendations:
            priority_colors = {"high": DANGER, "medium": WARNING, "low": SCORE_HIGH}
            p_color = priority_colors.get(rec.priority, DARK_TEXT)

            rec_data = [
                [Paragraph(
                    f'<font color="{p_color.hexval()}" size="9">'
                    f'\u25cf {rec.priority.upper()} PRIORITY</font>'
                    f'&nbsp;&nbsp;&nbsp;'
                    f'<font size="13"><b>{rec.service}</b></font>',
                    styles["BodyText2"])],
                [Spacer(1, 6)],
                [Paragraph(rec.rationale, styles["BodyText2"])],
                [Spacer(1, 6)],
                [Paragraph("<b>Action Items:</b>", styles["BodyText2"])],
            ]

            for action in rec.action_items:
                rec_data.append([
                    Paragraph(f"  \u2022  {action}", styles["BulletItem"]),
                ])

            rec_table = Table(rec_data, colWidths=[_CONTENT_WIDTH - 0.2 * inch])
            rec_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("BOX", (0, 0), (-1, -1), 1, p_color),
                ("LINEABOVE", (0, 0), (-1, 0), 3, p_color),
            ]))
            elements.append(rec_table)
            elements.append(Spacer(1, 18))

    return elements


# ── 8. Source Appendix ────────────────────────────────────

def _build_source_appendix(report: GEOReport, styles) -> list:
    elements = []

    if not report.all_sources:
        return elements

    elements.append(PageBreak())
    elements.extend(_section_header("Appendix: Complete Source List", styles))

    elements.append(Paragraph(
        f"Total unique sources: <b>{len(report.all_sources)}</b>",
        styles["BodyText2"]
    ))
    elements.append(Spacer(1, 14))

    # Group by category
    by_category = {}
    for s in report.all_sources:
        cat = s.category.value
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(s)

    for cat_name, sources in sorted(by_category.items()):
        elements.append(Paragraph(
            f"{cat_name} ({len(sources)} source{'s' if len(sources) != 1 else ''})",
            styles["SubsectionTitle"]
        ))
        elements.append(Spacer(1, 6))

        source_data = [[
            Paragraph("#", styles["TableHeader"]),
            Paragraph("Domain", styles["TableHeader"]),
            Paragraph("URL", styles["TableHeader"]),
        ]]

        for idx, src in enumerate(sources[:30], 1):
            url_display = src.url[:65] + "..." if len(src.url) > 65 else src.url
            source_data.append([
                Paragraph(str(idx), styles["TableCell"]),
                Paragraph(src.domain or "\u2014", styles["TableCell"]),
                Paragraph(
                    f'<font color="{SECONDARY.hexval()}">{url_display}</font>',
                    styles["SourceURL"]),
            ])

        st = Table(source_data, colWidths=[0.35 * inch, 1.5 * inch, _CONTENT_WIDTH - 1.95 * inch])
        st.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.3, DARK_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [DARK_CARD, DARK_TABLE_ALT]),
        ]))
        elements.append(st)
        elements.append(Spacer(1, 16))

    return elements


# ── Helpers ──────────────────────────────────────────────

def _generate_key_findings(report: GEOReport) -> list[str]:
    """Generate key findings for the executive summary."""
    findings = []
    vis = report.brand_visibility

    if not vis:
        return ["Insufficient data to generate findings."]

    score_desc = (
        "strong" if vis.overall_score >= 0.6
        else "moderate" if vis.overall_score >= 0.3
        else "weak"
    )
    findings.append(
        f"{report.brand_input.brand_name} has {score_desc} overall visibility "
        f"({vis.overall_score:.0%}) across AI models."
    )

    if vis.by_provider:
        best_prov = max(vis.by_provider, key=vis.by_provider.get)
        worst_prov = min(vis.by_provider, key=vis.by_provider.get)
        if vis.by_provider[best_prov] > vis.by_provider[worst_prov]:
            findings.append(
                f"Strongest visibility on {best_prov} ({vis.by_provider[best_prov]:.0%}), "
                f"weakest on {worst_prov} ({vis.by_provider[worst_prov]:.0%})."
            )

    if vis.by_category:
        best_cat = max(vis.by_category, key=vis.by_category.get)
        worst_cat = min(vis.by_category, key=vis.by_category.get)
        if vis.by_category[best_cat] > vis.by_category[worst_cat]:
            findings.append(
                f"Best performance in {best_cat} queries ({vis.by_category[best_cat]:.0%}), "
                f"needs improvement in {worst_cat} ({vis.by_category[worst_cat]:.0%})."
            )

    if report.competitor_visibility:
        better_competitors = [
            name for name, cv in report.competitor_visibility.items()
            if cv.overall_score > vis.overall_score
        ]
        if better_competitors:
            findings.append(
                f"{', '.join(better_competitors)} currently outperform "
                f"{report.brand_input.brand_name} in AI visibility."
            )
        else:
            findings.append(
                f"{report.brand_input.brand_name} outperforms all analyzed competitors."
            )

    if report.source_counts_by_category:
        num_types = len(report.source_counts_by_category)
        findings.append(
            f"Sources span {num_types} content categories across "
            f"{len(report.all_sources)} unique URLs."
        )

    return findings

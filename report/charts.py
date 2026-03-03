from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.units import inch
from report.styles import (
    PRIMARY, SECONDARY, ACCENT, WARNING, DANGER, LIGHT_BG, LIGHT, WHITE,
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER, CARD_BG, SOURCE_COLORS,
    SCORE_HIGH, SCORE_MEDIUM, SCORE_LOW, get_score_color,
    DARK_BG, DARK_CARD, DARK_BORDER, DARK_TEXT, DARK_TEXT_MUTED, DARK_TABLE_ALT,
)


def create_visibility_bar_chart(
    scores: dict,
    width: float = 450,
    height: float = 200,
    title: str = "",
) -> Drawing:
    """Create a horizontal bar chart for visibility scores."""
    d = Drawing(width, height)

    if not scores:
        d.add(String(width / 2, height / 2, "No data available",
                      fontSize=12, textAnchor="middle", fillColor=DARK_TEXT_MUTED))
        return d

    labels = list(scores.keys())
    values = [scores[k] * 100 for k in labels]  # Convert to percentage

    # Draw title
    if title:
        d.add(String(10, height - 15, title,
                      fontSize=11, fontName="Helvetica-Bold", fillColor=DARK_TEXT))

    # Draw bars manually for more control
    bar_height = 22
    max_bar_width = width - 160
    y_start = height - 40
    label_x = 5
    bar_x = 130

    for i, (label, value) in enumerate(zip(labels, values)):
        y = y_start - (i * (bar_height + 10))
        if y < 10:
            break

        # Truncate label
        display_label = label[:20] + "..." if len(label) > 20 else label

        # Label
        d.add(String(label_x, y + 6, display_label,
                      fontSize=8, fontName="Helvetica", fillColor=DARK_TEXT))

        # Background bar (dark themed)
        d.add(Rect(bar_x, y, max_bar_width, bar_height,
                    fillColor=DARK_CARD, strokeColor=None))

        # Value bar
        bar_w = max(2, (value / 100) * max_bar_width)
        color = get_score_color(value / 100)
        d.add(Rect(bar_x, y, bar_w, bar_height,
                    fillColor=color, strokeColor=None))

        # Value text
        d.add(String(bar_x + max_bar_width + 5, y + 6, f"{value:.0f}%",
                      fontSize=9, fontName="Helvetica-Bold", fillColor=color))

    return d


def create_source_pie_chart(
    source_counts: dict,
    width: float = 300,
    height: float = 250,
) -> Drawing:
    """Create a pie chart for source type distribution."""
    d = Drawing(width, height)

    if not source_counts:
        d.add(String(width / 2, height / 2, "No sources found",
                      fontSize=12, textAnchor="middle", fillColor=DARK_TEXT_MUTED))
        return d

    pie = Pie()
    pie.x = 40
    pie.y = 30
    pie.width = 140
    pie.height = 140

    labels = list(source_counts.keys())
    values = list(source_counts.values())
    pie.data = values
    pie.labels = None  # We'll add a legend instead

    # Assign colors
    for i, label in enumerate(labels):
        color = SOURCE_COLORS.get(label, HexColor("#9CA3AF"))
        pie.slices[i].fillColor = color
        pie.slices[i].strokeColor = DARK_BG
        pie.slices[i].strokeWidth = 1.5

    d.add(pie)

    # Add legend
    legend_x = 200
    legend_y = height - 30
    total = sum(values)

    for i, (label, value) in enumerate(zip(labels, values)):
        y = legend_y - (i * 16)
        if y < 10:
            break

        color = SOURCE_COLORS.get(label, HexColor("#9CA3AF"))
        d.add(Rect(legend_x, y - 3, 10, 10, fillColor=color, strokeColor=None))

        pct = (value / total * 100) if total > 0 else 0
        display = f"{label} ({value}, {pct:.0f}%)"
        if len(display) > 30:
            display = display[:27] + "..."
        d.add(String(legend_x + 14, y, display,
                      fontSize=7, fontName="Helvetica", fillColor=DARK_TEXT))

    return d


def create_comparison_heatmap_data(
    brand_name: str,
    brand_visibility: dict,
    competitor_visibility: dict,
    prompts: list[str],
) -> list:
    """
    Build data for a heatmap table.
    Returns list of rows: [entity_name, prompt1_score, prompt2_score, ...]
    """
    rows = []

    # Brand row
    brand_row = [brand_name]
    for prompt in prompts:
        score = brand_visibility.get(prompt, 0)
        brand_row.append(score)
    rows.append(brand_row)

    # Competitor rows
    for comp_name, comp_vis in competitor_visibility.items():
        row = [comp_name]
        for prompt in prompts:
            score = comp_vis.by_prompt.get(prompt, 0)
            row.append(score)
        rows.append(row)

    return rows


def create_mini_score_box(
    score: float,
    label: str,
    width: float = 100,
    height: float = 60,
) -> Drawing:
    """Create a mini score box with colored value."""
    d = Drawing(width, height)

    # Background — dark card
    d.add(Rect(0, 0, width, height, fillColor=DARK_CARD,
               strokeColor=DARK_BORDER, strokeWidth=0.5))

    # Score value
    color = get_score_color(score)
    d.add(String(width / 2, height - 25, f"{score:.0%}",
                  fontSize=20, fontName="Helvetica-Bold",
                  textAnchor="middle", fillColor=color))

    # Label
    display = label[:15] if len(label) > 15 else label
    d.add(String(width / 2, 8, display,
                  fontSize=7, fontName="Helvetica",
                  textAnchor="middle", fillColor=DARK_TEXT_MUTED))

    return d

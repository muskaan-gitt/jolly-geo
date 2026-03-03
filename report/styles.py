from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import inch

# ── Jolly Brand Colors ────────────────────────────────────
PRIMARY = HexColor("#140B08")       # Deep dark brown (background)
SECONDARY = HexColor("#E63600")     # Jolly red/orange (accent)
ACCENT = HexColor("#E63600")        # Same as secondary
LIGHT = HexColor("#F8F4F1")         # Off-white/cream

# Derived colors
WARNING = HexColor("#F59E0B")       # Amber
DANGER = HexColor("#E63600")        # Same as brand accent
LIGHT_BG = HexColor("#FAF8F6")      # Very light cream for table rows
WHITE = HexColor("#FFFFFF")
TEXT_PRIMARY = HexColor("#140B08")   # Dark text on light backgrounds
TEXT_SECONDARY = HexColor("#6B5E58") # Muted brown-grey
BORDER = HexColor("#E0D8D2")        # Warm grey border
CARD_BG = HexColor("#F5F0ED")       # Card background

# Dark-theme colors for PDF (matches dashboard)
DARK_BG = HexColor("#140B08")       # Page background (same as PRIMARY)
DARK_CARD = HexColor("#1E1210")     # Card / elevated surface on dark bg
DARK_BORDER = HexColor("#3D2E28")   # Subtle border on dark bg
DARK_TEXT = HexColor("#F8F4F1")     # Light text on dark backgrounds
DARK_TEXT_MUTED = HexColor("#A89890")  # Muted text on dark backgrounds
DARK_TABLE_ALT = HexColor("#251C18")   # Alternating table row on dark bg

# Score colors
SCORE_HIGH = HexColor("#22C55E")    # Green (>60%)
SCORE_MEDIUM = HexColor("#F59E0B")  # Amber (30-60%)
SCORE_LOW = HexColor("#E63600")     # Jolly red (<30%)

# Source category colors (warm palette)
SOURCE_COLORS = {
    "Official Site": HexColor("#E63600"),
    "Blog": HexColor("#8B5CF6"),
    "News": HexColor("#EC4899"),
    "Review Site": HexColor("#F59E0B"),
    "Forum / Community": HexColor("#22C55E"),
    "Social Media": HexColor("#06B6D4"),
    "Wiki / Encyclopedia": HexColor("#6366F1"),
    "E-commerce": HexColor("#F97316"),
    "Video": HexColor("#EF4444"),
    "Other": HexColor("#9CA3AF"),
}


def get_score_color(score: float) -> Color:
    if score >= 0.6:
        return SCORE_HIGH
    elif score >= 0.3:
        return SCORE_MEDIUM
    else:
        return SCORE_LOW


def get_styles():
    """Return custom paragraph styles for the PDF report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=36,
        textColor=LIGHT,
        alignment=TA_CENTER,
        spaceAfter=16,
        leading=42,
    ))

    styles.add(ParagraphStyle(
        name="CoverSubtitle",
        fontName="Helvetica",
        fontSize=16,
        textColor=HexColor("#C4B5AD"),
        alignment=TA_CENTER,
        spaceAfter=8,
        leading=20,
    ))

    styles.add(ParagraphStyle(
        name="CoverDate",
        fontName="Helvetica",
        fontSize=11,
        textColor=HexColor("#8A7E7A"),
        alignment=TA_CENTER,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=DARK_TEXT,
        spaceBefore=28,
        spaceAfter=12,
        leading=24,
    ))

    styles.add(ParagraphStyle(
        name="SubsectionTitle",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=SECONDARY,
        spaceBefore=18,
        spaceAfter=10,
        leading=17,
    ))

    styles.add(ParagraphStyle(
        name="BodyText2",
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_TEXT,
        spaceBefore=4,
        spaceAfter=6,
        leading=14,
    ))

    styles.add(ParagraphStyle(
        name="ReportIntro",
        fontName="Helvetica",
        fontSize=11,
        textColor=DARK_TEXT_MUTED,
        spaceBefore=6,
        spaceAfter=16,
        leading=16,
    ))

    styles.add(ParagraphStyle(
        name="SmallText",
        fontName="Helvetica",
        fontSize=8,
        textColor=DARK_TEXT_MUTED,
        leading=10,
    ))

    styles.add(ParagraphStyle(
        name="BulletItem",
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_TEXT,
        leftIndent=20,
        spaceBefore=4,
        spaceAfter=4,
        leading=14,
        bulletIndent=8,
    ))

    styles.add(ParagraphStyle(
        name="PromptText",
        fontName="Helvetica-Oblique",
        fontSize=11,
        textColor=DARK_TEXT_MUTED,
        spaceBefore=8,
        spaceAfter=8,
        leading=15,
        leftIndent=10,
        borderPadding=8,
    ))

    styles.add(ParagraphStyle(
        name="MetricValue",
        fontName="Helvetica-Bold",
        fontSize=28,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        leading=34,
    ))

    styles.add(ParagraphStyle(
        name="MetricLabel",
        fontName="Helvetica",
        fontSize=9,
        textColor=DARK_TEXT_MUTED,
        alignment=TA_CENTER,
        leading=12,
    ))

    styles.add(ParagraphStyle(
        name="TableHeader",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=LIGHT,
        leading=12,
    ))

    styles.add(ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=8,
        textColor=DARK_TEXT,
        leading=11,
    ))

    styles.add(ParagraphStyle(
        name="SourceURL",
        fontName="Helvetica",
        fontSize=7,
        textColor=SECONDARY,
        leading=10,
    ))

    styles.add(ParagraphStyle(
        name="PriorityHigh",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=DANGER,
        leading=12,
    ))

    styles.add(ParagraphStyle(
        name="PriorityMedium",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=WARNING,
        leading=12,
    ))

    styles.add(ParagraphStyle(
        name="PriorityLow",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=SCORE_HIGH,
        leading=12,
    ))

    styles.add(ParagraphStyle(
        name="Footer",
        fontName="Helvetica",
        fontSize=8,
        textColor=DARK_TEXT_MUTED,
        alignment=TA_CENTER,
    ))

    return styles

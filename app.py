import os
import sys
import base64
import streamlit as st
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.data_models import (
    BrandInput, GEOReport, PromptCategory, LLMProvider,
)
from core.scraper import scrape_brand_description, research_brand_description, extract_domain
from core.prompt_engine import build_prompt_set
from core.competitor_discovery import discover_competitors
from core.llm_runner import run_all_prompts
from analysis.visibility import analyze_brand_visibility, analyze_competitor_visibility
from analysis.source_parser import categorize_all_sources, get_source_counts, get_top_domains
from analysis.weak_points import identify_weak_points
from analysis.strategy import generate_recommendations
from report.pdf_generator import generate_pdf
from core.sheets_client import save_user, attach_report
from config.settings import PERSONAL_EMAIL_DOMAINS

load_dotenv()

# ── Brand Constants ────────────────────────────────────────
BRAND_BG = "#140B08"
BRAND_ACCENT = "#E63600"
BRAND_LIGHT = "#F8F4F1"
BRAND_CARD_BG = "#1E1210"
BRAND_BORDER = "#2A1A15"
BRAND_MUTED = "#8A7E7A"

# ── Page Config ─────────────────────────────────────────────

st.set_page_config(
    page_title="GEO Visibility Report | Jolly",
    page_icon="https://jollyseo.com/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load Logo ──────────────────────────────────────────────

def _load_logo() -> str:
    """Load Jolly logo SVG and return as base64 data URI."""
    logo_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "assets",
        "jolly_logo_sidebar.svg",
    )
    try:
        with open(logo_path, "r") as f:
            svg = f.read()
        b64 = base64.b64encode(svg.encode()).decode()
        return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        return ""


# ── Styling ─────────────────────────────────────────────────

st.markdown(f"""
<style>
    /* ── Global ─────────────────────────────────── */
    .stApp {{
        background-color: {BRAND_BG};
        color: {BRAND_LIGHT};
    }}
    header[data-testid="stHeader"] {{
        background-color: {BRAND_BG};
    }}
    .stApp [data-testid="stSidebar"] {{
        background-color: {BRAND_CARD_BG};
        border-right: 1px solid {BRAND_BORDER};
    }}
    .stApp [data-testid="stSidebar"] * {{
        color: {BRAND_LIGHT} !important;
    }}

    /* ── Typography ─────────────────────────────── */
    .main-header {{
        font-size: 2rem;
        font-weight: 700;
        color: {BRAND_LIGHT};
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }}
    .sub-header {{
        font-size: 1rem;
        color: {BRAND_MUTED};
        margin-bottom: 1.5rem;
    }}
    .section-title {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {BRAND_LIGHT};
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid {BRAND_ACCENT};
        display: inline-block;
    }}

    /* ── Metric Cards ───────────────────────────── */
    .metric-card {{
        background: {BRAND_CARD_BG};
        border-radius: 12px;
        padding: 24px 16px;
        text-align: center;
        border: 1px solid {BRAND_BORDER};
    }}
    .metric-value {{
        font-size: 2.8rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 6px;
    }}
    .metric-label {{
        font-size: 0.8rem;
        color: {BRAND_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .score-high {{ color: #22C55E; }}
    .score-medium {{ color: #F59E0B; }}
    .score-low {{ color: {BRAND_ACCENT}; }}

    /* ── Progress Bar ───────────────────────────── */
    .stProgress > div > div > div {{
        background-color: {BRAND_ACCENT};
    }}

    /* ── Buttons ────────────────────────────────── */
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"] {{
        background-color: {BRAND_ACCENT} !important;
        color: {BRAND_LIGHT} !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: opacity 0.2s !important;
    }}
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {{
        opacity: 0.9 !important;
        background-color: {BRAND_ACCENT} !important;
    }}

    /* ── Inputs ─────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background-color: {BRAND_CARD_BG} !important;
        color: {BRAND_LIGHT} !important;
        border: 1px solid {BRAND_BORDER} !important;
        border-radius: 8px !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {BRAND_ACCENT} !important;
        box-shadow: 0 0 0 1px {BRAND_ACCENT} !important;
    }}
    .stTextInput label, .stTextArea label {{
        color: {BRAND_MUTED} !important;
    }}

    /* ── Tabs ───────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        background-color: {BRAND_CARD_BG};
        border-radius: 10px;
        padding: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {BRAND_MUTED};
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {BRAND_ACCENT} !important;
        color: {BRAND_LIGHT} !important;
    }}

    /* ── Expander ───────────────────────────────── */
    .streamlit-expanderHeader {{
        background-color: {BRAND_CARD_BG} !important;
        color: {BRAND_LIGHT} !important;
        border-radius: 8px !important;
    }}

    /* ── Dataframe ──────────────────────────────── */
    .stDataFrame {{
        border-radius: 8px;
        overflow: hidden;
    }}

    /* ── Divider ────────────────────────────────── */
    hr {{
        border-color: {BRAND_BORDER} !important;
    }}

    /* ── Sidebar Logo ──────────────────────────── */
    .sidebar-logo {{
        margin-bottom: 0.25rem;
    }}
    .sidebar-logo img {{
        width: 150px;
    }}
    .sidebar-tagline {{
        font-size: 0.7rem;
        color: {BRAND_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }}
    .sidebar-section-title {{
        font-size: 0.65rem;
        font-weight: 600;
        color: {BRAND_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }}
    .api-status {{
        font-size: 0.85rem;
        padding: 3px 0;
    }}
    .service-tag {{
        display: inline-block;
        background: {BRAND_BG};
        border: 1px solid {BRAND_BORDER};
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.72rem;
        color: {BRAND_MUTED};
        margin: 2px 2px;
    }}

</style>
""", unsafe_allow_html=True)


# ── Session State ───────────────────────────────────────────

if "step" not in st.session_state:
    st.session_state.step = "input"
if "report" not in st.session_state:
    st.session_state.report = None
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "user_registered" not in st.session_state:
    st.session_state.user_registered = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}


# ── Sidebar ─────────────────────────────────────────────────

logo_uri = _load_logo()

with st.sidebar:
    if logo_uri:
        st.markdown(
            f'<div class="sidebar-logo"><img src="{logo_uri}" alt="Jolly"></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown("### Jolly.")

    st.markdown(
        '<div class="sidebar-tagline">GEO Visibility Monitor</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # API Key status
    st.markdown(
        '<div class="sidebar-section-title">Connected Models</div>',
        unsafe_allow_html=True,
    )
    api_keys = {
        "openai": os.getenv("OPENAI_API_KEY", ""),
        "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
        "gemini": os.getenv("GOOGLE_API_KEY", ""),
        "perplexity": os.getenv("PERPLEXITY_API_KEY", ""),
    }
    display_names = {
        "openai": "ChatGPT",
        "anthropic": "Claude",
        "gemini": "Gemini",
        "perplexity": "Perplexity",
    }
    for name, key in api_keys.items():
        icon = "●" if key else "○"
        color = "#22C55E" if key else BRAND_MUTED
        st.markdown(
            f'<div class="api-status"><span style="color:{color}">{icon}</span> {display_names[name]}</div>',
            unsafe_allow_html=True,
        )

    active_count = sum(1 for k in api_keys.values() if k)
    if active_count == 0:
        st.error("No API keys found. Create a .env file.")
    elif active_count < 4:
        st.caption(f"{active_count}/4 models active")

    st.markdown("---")

    st.markdown(
        '<div class="sidebar-section-title">Optimization Services</div>',
        unsafe_allow_html=True,
    )
    services = ["Backlinks", "Community", "Blogs", "PR & News", "Reviews"]
    tags_html = "".join(f'<span class="service-tag">{s}</span>' for s in services)
    st.markdown(tags_html, unsafe_allow_html=True)

    if st.session_state.step != "input":
        st.markdown("---")
        if st.button("New Analysis", use_container_width=True):
            st.session_state.step = "input"
            st.session_state.report = None
            st.session_state.pdf_path = None
            st.rerun()


# ── Main Content ────────────────────────────────────────────

def main():
    if st.session_state.step == "input":
        render_input_step()
    elif st.session_state.step == "processing":
        render_processing_step()
    elif st.session_state.step == "results":
        render_results_step()


# ── Registration Dialog ─────────────────────────────────────

@st.dialog("Register to Run Your Analysis")
def registration_dialog():
    st.caption("All fields are required. Please use your company email.")

    reg_name = st.text_input("Full Name *", key="reg_name", placeholder="Jane Smith")
    reg_position = st.text_input("Position / Role *", key="reg_position", placeholder="Marketing Manager")
    reg_company = st.text_input("Company Name *", key="reg_company", placeholder="Acme Corp")
    reg_website = st.text_input("Company Website *", key="reg_website", placeholder="https://acme.com")
    reg_email = st.text_input("Company Email *", key="reg_email", placeholder="jane@acme.com")

    if st.button("Continue to Analysis", type="primary", use_container_width=True):
        # Validate all fields are filled
        if not reg_name or not reg_name.strip():
            st.error("Please enter your name.")
            return
        if not reg_position or not reg_position.strip():
            st.error("Please enter your position.")
            return
        if not reg_company or not reg_company.strip():
            st.error("Please enter your company name.")
            return
        if not reg_website or not reg_website.strip():
            st.error("Please enter your company website.")
            return
        if not reg_email or not reg_email.strip():
            st.error("Please enter your company email.")
            return

        # Validate email format
        email_clean = reg_email.strip().lower()
        if "@" not in email_clean:
            st.error("Please enter a valid email address.")
            return

        email_domain = email_clean.split("@")[1]
        if email_domain in PERSONAL_EMAIL_DOMAINS:
            st.error("Please use your company email address, not a personal one.")
            return

        # Save to Google Sheets
        saved, err = save_user(
            name=reg_name.strip(),
            position=reg_position.strip(),
            company=reg_company.strip(),
            website=reg_website.strip(),
            email=email_clean,
        )
        if not saved:
            st.warning(f"Could not save registration data ({err}), but you can proceed.")

        st.session_state.user_registered = True
        st.session_state.user_info = {
            "name": reg_name.strip(),
            "position": reg_position.strip(),
            "company": reg_company.strip(),
            "website": reg_website.strip(),
            "email": email_clean,
        }
        st.session_state.step = "processing"
        st.rerun()


# ── Step 1: Input ───────────────────────────────────────────

def render_input_step():
    st.markdown(
        '<div class="main-header">GEO Visibility Monitor</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-header">'
        'Measure how your brand appears across ChatGPT, Claude, Gemini & Perplexity. '
        'Get a detailed visibility report with actionable recommendations.'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            '<div class="section-title">Brand Information</div>',
            unsafe_allow_html=True,
        )
        brand_name = st.text_input(
            "Brand / Product Name *",
            placeholder="e.g., Ahrefs, HubSpot, Notion",
        )
        website_url = st.text_input(
            "Website URL *",
            placeholder="e.g., https://ahrefs.com",
        )
        brand_description = st.text_area(
            "Brand Description (optional — auto-detected if blank)",
            placeholder="Brief description of what the brand/product does...",
            height=100,
        )

    with col2:
        st.markdown(
            '<div class="section-title">Competitors</div>',
            unsafe_allow_html=True,
        )
        st.caption("Up to 4 competitors. Leave blank to auto-discover via AI.")
        competitors_text = st.text_area(
            "Competitors (one per line)",
            placeholder="e.g.,\nSEMrush\nMoz\nSE Ranking\nSerpstat",
            height=150,
        )

    st.markdown("---")
    st.markdown(
        '<div class="section-title">Target Prompts</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Up to 3 prompts per intent category. Leave blank to auto-generate discovery prompts."
    )

    col_c, col_comp, col_i = st.columns(3)

    with col_c:
        st.markdown(f"**Commercial Intent**")
        c1 = st.text_input("Commercial prompt 1", key="c1", placeholder="e.g., Best SEO tool to buy in 2026")
        c2 = st.text_input("Commercial prompt 2", key="c2", placeholder="")
        c3 = st.text_input("Commercial prompt 3", key="c3", placeholder="")

    with col_comp:
        st.markdown(f"**Comparison Intent**")
        comp1 = st.text_input("Comparison prompt 1", key="comp1", placeholder="e.g., Ahrefs vs SEMrush")
        comp2 = st.text_input("Comparison prompt 2", key="comp2", placeholder="")
        comp3 = st.text_input("Comparison prompt 3", key="comp3", placeholder="")

    with col_i:
        st.markdown(f"**Informational Intent**")
        i1 = st.text_input("Informational prompt 1", key="i1", placeholder="e.g., How does backlink analysis work?")
        i2 = st.text_input("Informational prompt 2", key="i2", placeholder="")
        i3 = st.text_input("Informational prompt 3", key="i3", placeholder="")

    st.markdown("---")

    if st.button("Run Analysis", type="primary", use_container_width=True):
        if not brand_name:
            st.error("Please enter a brand name.")
            return
        if not website_url:
            st.error("Please enter a website URL.")
            return
        if not any(api_keys.values()):
            st.error("No API keys configured. Add at least one in your .env file.")
            return

        competitors = [c.strip() for c in competitors_text.split("\n") if c.strip()]
        user_prompts = {
            PromptCategory.COMMERCIAL: [p for p in [c1, c2, c3] if p.strip()],
            PromptCategory.COMPARISON: [p for p in [comp1, comp2, comp3] if p.strip()],
            PromptCategory.INFORMATIONAL: [p for p in [i1, i2, i3] if p.strip()],
        }

        st.session_state.input_data = {
            "brand_name": brand_name,
            "website_url": website_url,
            "brand_description": brand_description,
            "competitors": competitors,
            "user_prompts": user_prompts,
        }

        if st.session_state.user_registered:
            st.session_state.step = "processing"
            st.rerun()
        else:
            registration_dialog()


# ── Step 2: Processing ─────────────────────────────────────

def render_processing_step():
    if not st.session_state.user_registered:
        st.session_state.step = "input"
        st.rerun()

    st.markdown(
        '<div class="main-header">Analyzing Brand Visibility</div>',
        unsafe_allow_html=True,
    )

    data = st.session_state.input_data
    brand_name = data["brand_name"]
    website_url = data["website_url"]
    brand_description = data["brand_description"]
    competitors = data["competitors"]
    user_prompts = data["user_prompts"]

    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(completed, total, description):
        pct = completed / total if total > 0 else 0
        adjusted = 0.20 + (pct * 0.70)
        progress_bar.progress(min(adjusted, 0.99))
        status_text.text(description)

    try:
        # Step 1: Scrape description
        status_text.text("Extracting brand information...")
        progress_bar.progress(0.02)
        if not brand_description:
            brand_description = scrape_brand_description(website_url)
            if brand_description:
                st.info(f"Detected: {brand_description[:150]}...")
            else:
                if api_keys.get("anthropic"):
                    status_text.text("Researching brand via AI...")
                    brand_description = research_brand_description(
                        brand_name, website_url, api_keys["anthropic"]
                    )
                    if brand_description:
                        st.info(f"Researched: {brand_description[:150]}...")
                if not brand_description:
                    st.warning("Could not determine brand description. Using brand name as context.")
                    brand_description = brand_name
        progress_bar.progress(0.05)

        # Step 2: Discover competitors
        status_text.text("Identifying competitors...")
        if len(competitors) < 4 and api_keys.get("anthropic"):
            competitors = discover_competitors(
                brand_name, brand_description, website_url,
                competitors, api_keys["anthropic"]
            )
            st.info(f"Competitors: {', '.join(competitors)}")
        progress_bar.progress(0.10)

        # Step 3: Build prompts
        status_text.text("Generating discovery prompts...")
        prompts = build_prompt_set(
            brand_name, brand_description, competitors,
            user_prompts, api_keys.get("anthropic")
        )
        progress_bar.progress(0.20)

        with st.expander("View Target Prompts", expanded=False):
            for cat, prompt_list in prompts.items():
                st.markdown(f"**{cat.value}:**")
                for p in prompt_list:
                    st.markdown(f"  - {p}")

        brand_input = BrandInput(
            brand_name=brand_name,
            website_url=website_url,
            brand_description=brand_description,
            competitors=competitors,
            prompts=prompts,
        )

        # Step 4: Run LLM queries
        status_text.text("Querying AI models...")
        responses = run_all_prompts(brand_input, api_keys, progress_callback=update_progress)

        valid_responses = [r for r in responses if r.error is None]
        error_responses = [r for r in responses if r.error is not None]

        if error_responses:
            with st.expander(f"{len(error_responses)} API errors", expanded=False):
                for r in error_responses:
                    st.text(f"{r.provider.value}: {r.error[:100]}")

        progress_bar.progress(0.90)

        # Step 5: Analysis
        status_text.text("Computing visibility scores...")
        brand_visibility = analyze_brand_visibility(brand_name, responses)
        competitor_visibility = analyze_competitor_visibility(competitors, responses)

        brand_domain = extract_domain(website_url)
        all_sources = categorize_all_sources(responses, brand_domain)
        source_counts = get_source_counts(all_sources)

        weak_points = identify_weak_points(
            brand_name, competitors, responses,
            brand_visibility, competitor_visibility, all_sources
        )

        strategy_recommendations = generate_recommendations(
            weak_points, source_counts, brand_visibility, brand_name
        )

        progress_bar.progress(0.95)

        report = GEOReport(
            brand_input=brand_input,
            responses=responses,
            brand_visibility=brand_visibility,
            competitor_visibility=competitor_visibility,
            all_sources=all_sources,
            source_counts_by_category=source_counts,
            weak_points=weak_points,
            strategy_recommendations=strategy_recommendations,
        )

        # Step 6: Generate PDF
        status_text.text("Generating PDF report...")
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
        pdf_path = generate_pdf(report, output_dir)

        progress_bar.progress(1.0)
        status_text.text("Analysis complete!")

        # Attach report to user's registration in Google Sheets
        if st.session_state.user_registered and st.session_state.user_info:
            attach_report(
                email=st.session_state.user_info["email"],
                brand_name=brand_name,
                report_filename=os.path.basename(pdf_path),
            )

        st.session_state.report = report
        st.session_state.pdf_path = pdf_path
        st.session_state.step = "results"
        st.rerun()

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"An error occurred during analysis: {str(e)}")
        import traceback
        with st.expander("Error details"):
            st.code(traceback.format_exc())
        if st.button("Back to Input"):
            st.session_state.step = "input"
            st.rerun()


# ── Step 3: Results ─────────────────────────────────────────

def render_results_step():
    if not st.session_state.user_registered:
        st.session_state.step = "input"
        st.rerun()

    report = st.session_state.report
    pdf_path = st.session_state.pdf_path

    if not report:
        st.session_state.step = "input"
        st.rerun()
        return

    st.markdown(
        '<div class="main-header">Visibility Report</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="sub-header">'
        f'{report.brand_input.brand_name} &middot; {report.generated_at}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Download button
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="Download Full Report (PDF)",
                data=f.read(),
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

    st.markdown("---")

    # Overall metrics
    vis = report.brand_visibility
    if vis:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            score_class = (
                "score-high" if vis.overall_score >= 0.6
                else "score-medium" if vis.overall_score >= 0.3
                else "score-low"
            )
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value {score_class}">{vis.overall_score:.0%}</div>
                <div class="metric-label">Overall Visibility</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            valid = sum(1 for r in report.responses if r.error is None)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:{BRAND_LIGHT}">{valid}/{len(report.responses)}</div>
                <div class="metric-label">Valid Responses</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:{BRAND_LIGHT}">{len(report.all_sources)}</div>
                <div class="metric-label">Sources Found</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            wp_color = BRAND_ACCENT if report.weak_points else "#22C55E"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:{wp_color}">{len(report.weak_points)}</div>
                <div class="metric-label">Weak Points</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "By Provider", "Prompt Details", "Sources",
        "Competitors", "Strategy",
    ])

    with tab1:
        _render_provider_tab(report)
    with tab2:
        _render_prompt_tab(report)
    with tab3:
        _render_sources_tab(report)
    with tab4:
        _render_competitors_tab(report)
    with tab5:
        _render_strategy_tab(report)


def _render_provider_tab(report: GEOReport):
    vis = report.brand_visibility
    if not vis or not vis.by_provider:
        st.info("No provider data available.")
        return

    st.markdown(
        '<div class="section-title">Visibility by AI Model</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(vis.by_provider))
    for i, (provider, score) in enumerate(vis.by_provider.items()):
        with cols[i]:
            score_class = (
                "score-high" if score >= 0.6
                else "score-medium" if score >= 0.3
                else "score-low"
            )
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value {score_class}">{score:.0%}</div>
                <div class="metric-label">{provider}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown(
        '<div class="section-title">Visibility by Intent Category</div>',
        unsafe_allow_html=True,
    )
    if vis.by_category:
        cols = st.columns(len(vis.by_category))
        for i, (cat, score) in enumerate(vis.by_category.items()):
            with cols[i]:
                score_class = (
                    "score-high" if score >= 0.6
                    else "score-medium" if score >= 0.3
                    else "score-low"
                )
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value {score_class}">{score:.0%}</div>
                    <div class="metric-label">{cat}</div>
                </div>
                """, unsafe_allow_html=True)


def _render_prompt_tab(report: GEOReport):
    st.markdown(
        '<div class="section-title">Prompt-by-Prompt Results</div>',
        unsafe_allow_html=True,
    )

    prompt_idx = 0
    for category in PromptCategory:
        prompts = report.brand_input.prompts.get(category, [])
        for prompt_text in prompts:
            prompt_idx += 1
            prompt_responses = [
                r for r in report.responses
                if r.prompt == prompt_text and r.error is None
            ]

            with st.expander(f"P{prompt_idx} [{category.value}]: {prompt_text[:70]}..."):
                if not prompt_responses:
                    st.warning("No valid responses for this prompt.")
                    continue

                rows = []
                for r in prompt_responses:
                    comp_mentioned = [c for c, m in r.competitor_mentions.items() if m]
                    rows.append({
                        "Model": r.provider.value,
                        "Brand Mentioned": "Yes" if r.brand_mentioned else "No",
                        "Brand Cited": "Yes" if r.brand_cited else "No",
                        "Competitors Found": ", ".join(comp_mentioned) if comp_mentioned else "None",
                        "Sources": len(r.sources),
                    })
                st.dataframe(rows, use_container_width=True, hide_index=True)

                prompt_sources = []
                seen = set()
                for r in prompt_responses:
                    for s in r.sources:
                        if s.url not in seen:
                            seen.add(s.url)
                            prompt_sources.append(s)

                if prompt_sources:
                    st.markdown(f"**Sources ({len(prompt_sources)})**")
                    source_rows = [{
                        "Type": s.category.value,
                        "Domain": s.domain,
                        "URL": s.url,
                    } for s in prompt_sources]
                    st.dataframe(source_rows, use_container_width=True, hide_index=True)


def _render_sources_tab(report: GEOReport):
    st.markdown(
        '<div class="section-title">Source Analysis</div>',
        unsafe_allow_html=True,
    )

    if not report.all_sources:
        st.info("No sources found.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**By Category**")
        if report.source_counts_by_category:
            for cat, count in sorted(
                report.source_counts_by_category.items(), key=lambda x: -x[1]
            ):
                st.markdown(f"- **{cat}**: {count}")

    with col2:
        st.markdown("**Top Domains**")
        top_domains = get_top_domains(report.all_sources, 10)
        for domain, count in top_domains:
            st.markdown(f"- **{domain}**: {count}")

    st.markdown("---")
    st.markdown("**All Sources**")
    source_data = [{
        "Type": s.category.value,
        "Domain": s.domain,
        "Title": s.title[:50] if s.title else "",
        "URL": s.url,
    } for s in report.all_sources]
    st.dataframe(source_data, use_container_width=True, hide_index=True)


def _render_competitors_tab(report: GEOReport):
    st.markdown(
        '<div class="section-title">Competitor Comparison</div>',
        unsafe_allow_html=True,
    )

    vis = report.brand_visibility
    if not vis:
        st.info("No visibility data available.")
        return

    all_scores = {report.brand_input.brand_name: vis.overall_score}
    for comp_name, comp_vis in report.competitor_visibility.items():
        all_scores[comp_name] = comp_vis.overall_score

    st.markdown("**Overall Visibility Ranking**")
    for name, score in sorted(all_scores.items(), key=lambda x: -x[1]):
        is_brand = name == report.brand_input.brand_name
        label = f"**{name}** (You)" if is_brand else name
        st.progress(score, text=f"{label}: {score:.0%}")

    st.markdown("---")
    st.markdown("**Prompt-Level Heatmap**")

    all_prompts = []
    for cat in PromptCategory:
        all_prompts.extend(report.brand_input.prompts.get(cat, []))

    if all_prompts:
        heatmap = {}
        heatmap[report.brand_input.brand_name] = {
            f"P{i+1}": ("Yes" if vis.by_prompt.get(p, 0) > 0.5 else "No")
            for i, p in enumerate(all_prompts)
        }
        for comp_name, comp_vis in report.competitor_visibility.items():
            heatmap[comp_name] = {
                f"P{i+1}": ("Yes" if comp_vis.by_prompt.get(p, 0) > 0.5 else "No")
                for i, p in enumerate(all_prompts)
            }

        st.dataframe(heatmap, use_container_width=True)

        st.markdown("**Prompt Key**")
        for i, p in enumerate(all_prompts):
            st.caption(f"P{i+1}: {p}")


def _render_strategy_tab(report: GEOReport):
    st.markdown(
        '<div class="section-title">Weak Points & Strategy</div>',
        unsafe_allow_html=True,
    )

    if report.weak_points:
        st.markdown("**Identified Weak Points**")
        for i, wp in enumerate(report.weak_points, 1):
            with st.expander(f"Weak Point {i}: {wp.description[:80]}..."):
                st.markdown(f"**Description:** {wp.description}")
                if wp.prompt and not wp.prompt.startswith("["):
                    st.markdown(f"**Prompt:** {wp.prompt}")
                st.markdown(f"**Category:** {wp.prompt_category.value}")
                if wp.dominating_competitors:
                    st.markdown(
                        f"**Dominating Competitors:** {', '.join(wp.dominating_competitors)}"
                    )
                st.markdown(f"**Recommended Service:** {wp.recommended_service}")

    st.markdown("---")

    if report.strategy_recommendations:
        st.markdown("**Strategy Recommendations**")
        for rec in report.strategy_recommendations:
            priority_labels = {"high": "High Priority", "medium": "Medium Priority", "low": "Low Priority"}
            label = priority_labels.get(rec.priority, rec.priority)

            with st.expander(f"{label} — {rec.service}"):
                st.markdown(f"**Rationale:** {rec.rationale}")
                st.markdown("**Action Items:**")
                for action in rec.action_items:
                    st.markdown(f"- {action}")
    else:
        st.success("No critical weak points identified. Strong AI visibility across all models.")


if __name__ == "__main__":
    main()

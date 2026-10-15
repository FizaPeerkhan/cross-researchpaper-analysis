"""SciInsight Streamlit frontend.

The backend contract is intentionally unchanged:
- GET  /
- GET  /papers -> {"papers": [...]}
- POST /upload with multipart field "file" -> {"paper_id": ...}
- POST /extract/{paper_id}
- GET  /extract/{paper_id} -> existing extraction JSON
- POST /compare with a JSON list of paper IDs
- POST /gaps with a JSON list of paper IDs
- GET  /evidence with query parameters
"""

import os
from datetime import datetime

import requests
import streamlit as st

API_URL = os.getenv("SCINSIGHT_API_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = (5, 120)

PAGES = [
    "📤 Upload Papers",
    "📄 Paper Explorer",
    "📊 Cross-Paper Analysis",
    "🔍 Research Gaps",
    "🔎 Evidence Viewer",
]

st.set_page_config(
    page_title="SciInsight | Scientific Literature Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling: presentation only; does not alter API payloads ----------
st.markdown(
    """
    <style>
    :root {
        --si-ink: #172033;
        --si-muted: #64748b;
        --si-blue: #3157d5;
        --si-border: #e5eaf2;
        --si-panel: #f7f9fc;
    }
    .block-container { padding-top: 1.7rem; padding-bottom: 3rem; max-width: 1440px; }
    [data-testid="stSidebar"] { border-right: 1px solid var(--si-border); }
    .si-eyebrow {
        color: #3157d5; font-size: .78rem; font-weight: 750;
        letter-spacing: .13em; text-transform: uppercase; margin-bottom: .35rem;
    }
    .si-title { color: var(--si-ink); font-size: 2.15rem; font-weight: 800; line-height: 1.15; }
    .si-subtitle { color: var(--si-muted); font-size: 1rem; margin-top: .55rem; }
    .si-panel {
        background: var(--si-panel); border: 1px solid var(--si-border);
        border-radius: 14px; padding: 1rem 1.15rem; margin: .35rem 0 .8rem 0;
    }
    .si-evidence {
        background: #f0f8f4; border-left: 4px solid #23865b;
        border-radius: 0 10px 10px 0; padding: .85rem 1rem;
        margin: .45rem 0 .8rem 0; color: #173d2d;
    }
    .si-muted { color: var(--si-muted); font-size: .88rem; }
    div[data-testid="stMetric"] {
        background: var(--si-panel); border: 1px solid var(--si-border);
        padding: .9rem 1rem; border-radius: 12px;
    }
    div.stButton > button { border-radius: 9px; font-weight: 650; }
    div[data-testid="stFileUploader"] {
        border: 1px dashed #b8c5df; border-radius: 12px; padding: .5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- API helpers ----------
def api_request(method, path, *, params=None, json_body=None, files=None):
    """Call the existing API and return (response, error_message)."""
    try:
        response = requests.request(
            method=method,
            url=f"{API_URL}{path}",
            params=params,
            json=json_body,
            files=files,
            timeout=REQUEST_TIMEOUT,
        )
        if not response.ok:
            detail = response.text.strip()
            try:
                body = response.json()
                detail = body.get("detail", detail) if isinstance(body, dict) else detail
            except ValueError:
                pass
            return response, f"API returned {response.status_code}: {detail or response.reason}"
        return response, None
    except requests.exceptions.Timeout:
        return None, "The API request timed out. Large PDFs can take longer; please retry."
    except requests.exceptions.ConnectionError:
        return None, f"Cannot connect to the backend at {API_URL}. Start the API and retry."
    except requests.exceptions.RequestException as exc:
        return None, f"Request failed: {exc}"


def api_json(method, path, *, params=None, json_body=None, files=None):
    response, error = api_request(
        method, path, params=params, json_body=json_body, files=files
    )
    if error:
        return None, error
    try:
        return response.json(), None
    except ValueError:
        return None, "The API response was not valid JSON."


def fetch_papers():
    data, error = api_json("GET", "/papers")
    if error:
        return [], error
    if not isinstance(data, dict) or not isinstance(data.get("papers"), list):
        return [], "The /papers response did not contain the expected 'papers' list."
    return data["papers"], None


def paper_label(paper):
    return paper.get("title") or paper.get("filename") or str(paper.get("paper_id", "Unknown paper"))


def show_evidence(evidence, page_key="page_number"):
    """Render evidence without changing its source fields."""
    text = evidence.get("text", "")
    if text:
        st.markdown(f"> {text}")
    page = evidence.get(page_key, evidence.get("page", "?"))
    section = evidence.get("section")
    details = []
    if page not in (None, ""):
        details.append(f"Page {page}")
    if section:
        details.append(f"Section: {section}")
    if details:
        st.caption(" · ".join(details))


def render_item_list(items, *, title=None, show_evidence_items=False):
    if title:
        st.markdown(f"#### {title}")
    if not items:
        st.caption("No information extracted for this section.")
        return
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            value = item.get("value", item.get("text", str(item)))
            evidence = item.get("evidence", [])
            confidence = item.get("confidence")
        else:
            value, evidence, confidence = str(item), [], None

        with st.container(border=True):
            st.write(value)
            if confidence is not None:
                try:
                    st.caption(f"Confidence: {float(confidence):.2f}")
                except (TypeError, ValueError):
                    st.caption(f"Confidence: {confidence}")
            if evidence and show_evidence_items:
                with st.expander(f"View evidence ({len(evidence)})"):
                    for ev in evidence:
                        show_evidence(ev)


def render_empty_state(title, message, icon="📚"):
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")
        st.write(message)


def render_page_header(eyebrow, title, description):
    st.markdown(f'<div class="si-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="si-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="si-subtitle">{description}</div>', unsafe_allow_html=True)
    st.write("")


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🔬 SciInsight")
    st.caption("Scientific Literature Intelligence")
    st.divider()
    page = st.radio("WORKSPACE", PAGES, label_visibility="visible")
    st.divider()
    st.markdown("#### Backend status")
    status_placeholder = st.empty()
    health_response, health_error = api_request("GET", "/")
    if health_error:
        status_placeholder.error("Backend offline")
        with st.expander("Connection details"):
            st.caption(health_error)
    else:
        status_placeholder.success("Backend connected")
        st.caption(API_URL)
    st.divider()
    st.caption("Evidence-grounded analysis · Candidate gaps, not definitive claims")


# ---------- Upload Papers ----------
if page == "📤 Upload Papers":
    render_page_header(
        "WORKSPACE / INGESTION",
        "Your literature workspace",
        "Upload research PDFs, extract their scientific information, and track processing status.",
    )

    papers, papers_error = fetch_papers()
    if papers_error:
        st.error(papers_error)
    else:
        extracted_count = sum(bool(p.get("extracted")) for p in papers)
        m1, m2, m3 = st.columns(3)
        m1.metric("Papers in library", len(papers))
        m2.metric("Successfully extracted", extracted_count)
        m3.metric("Awaiting extraction", max(0, len(papers) - extracted_count))

    st.markdown("### Add research papers")
    uploaded_files = st.file_uploader(
        "Choose one or more PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Select text-based research PDFs. Scanned PDFs may need OCR support in the backend.",
        key="paper_uploader",
    )

    if uploaded_files:
        total_bytes = sum(file.size for file in uploaded_files)
        c1, c2 = st.columns(2)
        c1.info(f"{len(uploaded_files)} PDF(s) selected")
        c2.caption(f"Total size: {total_bytes / (1024 * 1024):.2f} MB")
        with st.expander("Review selected files"):
            for file in uploaded_files:
                st.write(f"📄 {file.name} · {file.size / 1024:.1f} KB")

        if st.button("Upload and extract selected papers", type="primary", use_container_width=True):
            progress = st.progress(0, text="Preparing uploads...")
            successes, failures = 0, []
            for index, uploaded_file in enumerate(uploaded_files):
                progress.progress(
                    int(index / len(uploaded_files) * 100),
                    text=f"Uploading {uploaded_file.name}...",
                )
                payload = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        "application/pdf",
                    )
                }
                result, error = api_json("POST", "/upload", files=payload)
                if error:
                    failures.append(f"{uploaded_file.name}: {error}")
                    continue

                paper_id = result.get("paper_id") if isinstance(result, dict) else None
                if paper_id is None:
                    failures.append(f"{uploaded_file.name}: upload response did not contain paper_id.")
                    continue

                _, extract_error = api_request("POST", f"/extract/{paper_id}")
                if extract_error:
                    failures.append(f"{uploaded_file.name}: uploaded (ID {paper_id}) but extraction failed: {extract_error}")
                else:
                    successes += 1

            progress.progress(100, text="Upload batch complete.")
            if successes:
                st.success(f"Successfully uploaded and extracted {successes} paper(s).")
            if failures:
                with st.expander(f"{len(failures)} item(s) need attention", expanded=True):
                    for failure in failures:
                        st.warning(failure)
            st.rerun()

    st.divider()
    header_col, refresh_col = st.columns([5, 1])
    with header_col:
        st.markdown("### Paper library")
    with refresh_col:
        if st.button("↻ Refresh", key="refresh_uploads"):
            st.rerun()

    papers, papers_error = fetch_papers()
    if papers_error:
        st.error(papers_error)
    elif not papers:
        render_empty_state("No papers yet", "Upload your first research PDF to begin.", "📥")
    else:
        for paper in papers:
            with st.container(border=True):
                title_col, status_col, action_col = st.columns([5, 1.4, 1.4])
                with title_col:
                    st.markdown(f"**{paper_label(paper)}**")
                    uploaded_at = paper.get("uploaded_at", "")
                    if uploaded_at:
                        st.caption(f"ID: {paper.get('paper_id', 'N/A')} · Uploaded: {str(uploaded_at)[:19]}")
                    else:
                        st.caption(f"Paper ID: {paper.get('paper_id', 'N/A')}")
                with status_col:
                    if paper.get("extracted"):
                        st.success("Extracted")
                    else:
                        st.warning("Pending")
                with action_col:
                    if not paper.get("extracted") and st.button(
                        "Extract", key=f"extract_{paper.get('paper_id')}", use_container_width=True
                    ):
                        with st.spinner(f"Extracting {paper_label(paper)}..."):
                            _, error = api_request("POST", f"/extract/{paper.get('paper_id')}")
                        if error:
                            st.error(error)
                        else:
                            st.success("Extraction completed.")
                        st.rerun()


# ---------- Paper Explorer ----------
elif page == "📄 Paper Explorer":
    render_page_header(
        "WORKSPACE / PAPER DETAIL",
        "Paper explorer",
        "Inspect extracted scientific information and open evidence behind supported fields.",
    )
    papers, error = fetch_papers()
    if error:
        st.error(error)
    else:
        extracted_papers = [p for p in papers if p.get("extracted")]
        if not extracted_papers:
            render_empty_state(
                "No extracted papers available",
                "Go to Upload Papers and extract at least one paper first.",
            )
        else:
            selected = st.selectbox(
                "Choose a paper",
                options=extracted_papers,
                format_func=paper_label,
                key="explorer_selected_paper",
            )
            if selected:
                extraction, error = api_json("GET", f"/extract/{selected['paper_id']}")
                if error:
                    st.error(error)
                elif isinstance(extraction, dict):
                    st.markdown(f"## {extraction.get('title') or paper_label(selected)}")
                    st.caption(f"Paper ID: {extraction.get('paper_id', selected.get('paper_id', 'N/A'))}")
                    sections = [
                        ("🎯 Problem", "problem"),
                        ("🔧 Methods", "methods"),
                        ("📊 Datasets", "datasets"),
                        ("📋 Tasks", "tasks"),
                        ("📈 Metrics", "metrics"),
                        ("⚠️ Limitations", "limitations"),
                        ("🔮 Future work", "future_work"),
                    ]
                    counts = {
                        label: len(extraction.get(key, []) or [])
                        for label, key in sections
                    }
                    metric_cols = st.columns(4)
                    for col, (label, count) in zip(metric_cols, list(counts.items())[:4]):
                        col.metric(label, count)

                    tab_labels = [label for label, _ in sections]
                    tabs = st.tabs(tab_labels)
                    for tab, (label, key) in zip(tabs, sections):
                        with tab:
                            items = extraction.get(key, []) or []
                            if key in ("methods", "limitations"):
                                render_item_list(items, show_evidence_items=True)
                            else:
                                render_item_list(items)


# ---------- Cross-Paper Analysis ----------
elif page == "📊 Cross-Paper Analysis":
    render_page_header(
        "WORKSPACE / SYNTHESIS",
        "Cross-paper analysis",
        "Compare methods, datasets, limitations and trends across a selected set of extracted papers.",
    )
    papers, error = fetch_papers()
    if error:
        st.error(error)
    else:
        extracted_papers = [p for p in papers if p.get("extracted")]
        if len(extracted_papers) < 2:
            render_empty_state(
                "More papers needed",
                "Extract at least two papers before running cross-paper analysis.",
            )
        else:
            selected_ids = st.multiselect(
                "Papers to compare",
                options=[p["paper_id"] for p in extracted_papers],
                format_func=lambda pid: next(
                    (paper_label(p) for p in extracted_papers if p.get("paper_id") == pid),
                    str(pid),
                ),
                default=[p["paper_id"] for p in extracted_papers[:5]],
                key="compare_selected_ids",
            )
            st.caption(f"{len(selected_ids)} paper(s) selected. Select at least 2 to compare.")
            if st.button(
                "Analyze selected papers",
                type="primary",
                disabled=len(selected_ids) < 2,
                use_container_width=True,
            ):
                with st.spinner("Comparing extracted information..."):
                    result, error = api_json("POST", "/compare", json_body=selected_ids)
                if error:
                    st.error(error)
                else:
                    st.session_state["last_comparison_result"] = result
                    st.session_state["last_comparison_ids"] = selected_ids

            result = st.session_state.get("last_comparison_result")
            if result and st.session_state.get("last_comparison_ids") == selected_ids:
                comparison = result.get("comparison", {})
                trends = result.get("trends", {}) or {}
                common_methods = comparison.get("common_methods", {}) or {}
                common_datasets = comparison.get("common_datasets", {}) or {}
                common_lims = comparison.get("common_limitations", {}) or {}

                summary_cols = st.columns(3)
                summary_cols[0].metric("Methods shared across papers", len(common_methods))
                summary_cols[1].metric("Datasets shared across papers", len(common_datasets))
                summary_cols[2].metric("Limitation categories", len(common_lims))

                left, right = st.columns(2)
                with left:
                    st.markdown("### Common methods")
                    if common_methods:
                        for method, paper_ids in sorted(common_methods.items(), key=lambda x: -len(x[1])):
                            st.write(f"**{method}** · {len(paper_ids)} paper(s)")
                    else:
                        st.info("No common methods found.")
                    st.markdown("### Common datasets")
                    if common_datasets:
                        for dataset, paper_ids in sorted(common_datasets.items(), key=lambda x: -len(x[1])):
                            st.write(f"**{dataset}** · {len(paper_ids)} paper(s)")
                    else:
                        st.info("No common datasets found.")
                with right:
                    st.markdown("### Common limitations")
                    if common_lims:
                        for lim_type, paper_ids in sorted(common_lims.items(), key=lambda x: -len(x[1])):
                            st.write(f"**{str(lim_type).replace('_', ' ').title()}** · {len(paper_ids)} paper(s)")
                    else:
                        st.info("No common limitations found.")
                    st.markdown("### Emerging methods")
                    emerging = trends.get("emerging_methods", []) or []
                    if emerging:
                        for method in emerging[:5]:
                            st.write(f"**{method.get('value', 'Unknown')}** · {method.get('frequency', 0):.0%}")
                    else:
                        st.caption("No emerging-method trend was returned.")

                method_freq = trends.get("method_frequency", {}) or {}
                dataset_freq = trends.get("dataset_frequency", {}) or {}
                if method_freq or dataset_freq:
                    st.markdown("### Frequency overview")
                    try:
                        import pandas as pd
                        import plotly.express as px

                        chart_left, chart_right = st.columns(2)
                        with chart_left:
                            if method_freq:
                                df = pd.DataFrame(
                                    sorted(method_freq.items(), key=lambda x: -x[1])[:10],
                                    columns=["Method", "Count"],
                                )
                                fig = px.bar(df, x="Count", y="Method", orientation="h", title="Most frequent methods")
                                fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=10, r=10, t=50, b=10))
                                st.plotly_chart(fig, use_container_width=True)
                        with chart_right:
                            if dataset_freq:
                                df = pd.DataFrame(
                                    sorted(dataset_freq.items(), key=lambda x: -x[1])[:10],
                                    columns=["Dataset", "Count"],
                                )
                                fig = px.bar(df, x="Count", y="Dataset", orientation="h", title="Most frequent datasets")
                                fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=10, r=10, t=50, b=10))
                                st.plotly_chart(fig, use_container_width=True)
                    except ImportError:
                        st.info("Install pandas and plotly to display charts; textual analysis is still available.")
                with st.expander("View raw API response"):
                    st.json(result)


# ---------- Research Gaps ----------
elif page == "🔍 Research Gaps":
    render_page_header(
        "WORKSPACE / OPPORTUNITIES",
        "Candidate research gaps",
        "Identify recurring limitations and potential directions across papers. These are hypotheses to investigate, not proven gaps.",
    )
    papers, error = fetch_papers()
    if error:
        st.error(error)
    else:
        extracted_papers = [p for p in papers if p.get("extracted")]
        if len(extracted_papers) < 2:
            render_empty_state(
                "More papers needed",
                "Extract at least two papers before running gap analysis.",
            )
        else:
            selected_ids = st.multiselect(
                "Papers for gap analysis",
                options=[p["paper_id"] for p in extracted_papers],
                format_func=lambda pid: next(
                    (paper_label(p) for p in extracted_papers if p.get("paper_id") == pid),
                    str(pid),
                ),
                default=[p["paper_id"] for p in extracted_papers[:5]],
                key="gaps_selected_ids",
            )
            st.caption(f"{len(selected_ids)} paper(s) selected.")
            if st.button(
                "Detect candidate gaps",
                type="primary",
                disabled=len(selected_ids) < 2,
                use_container_width=True,
            ):
                with st.spinner("Analyzing recurring limitations and evidence..."):
                    result, error = api_json("POST", "/gaps", json_body=selected_ids)
                if error:
                    st.error(error)
                else:
                    st.session_state["last_gaps_result"] = result
                    st.session_state["last_gaps_ids"] = selected_ids

            result = st.session_state.get("last_gaps_result")
            if result and st.session_state.get("last_gaps_ids") == selected_ids:
                analyzed = result.get("num_papers_analyzed", len(selected_ids))
                st.success(f"Analysis completed for {analyzed} paper(s).")
                notes = result.get("methodology_notes")
                if notes:
                    st.info(notes)
                gaps = result.get("gaps", []) or []
                if not gaps:
                    st.info("No significant candidate gaps were returned.")
                else:
                    st.markdown(f"### {len(gaps)} candidate direction(s)")
                    for index, gap in enumerate(gaps, start=1):
                        confidence = str(gap.get("confidence", "unknown")).lower()
                        icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(confidence, "⚪")
                        description = gap.get("description", "Undescribed gap")
                        with st.expander(f"{icon} {index}. {description[:100]}", expanded=index == 1):
                            detail_col, meta_col = st.columns([2, 1])
                            with detail_col:
                                st.markdown("**Description**")
                                st.write(description)
                                st.markdown("**Suggested direction**")
                                st.write(gap.get("suggested_direction", "Not provided"))
                            with meta_col:
                                st.markdown("**Gap type**")
                                st.write(gap.get("gap_type", "Not specified"))
                                st.markdown("**Confidence**")
                                st.write(gap.get("confidence", "Not specified"))
                                st.markdown("**Supporting papers**")
                                st.write(gap.get("frequency", "Not specified"))
                            related = gap.get("related_limitations", []) or []
                            if related:
                                st.markdown("**Related limitations**")
                                st.write(", ".join(map(str, related)))
                            evidence = gap.get("evidence", []) or []
                            if evidence:
                                st.markdown("**Supporting evidence**")
                                for ev in evidence:
                                    with st.container(border=True):
                                        show_evidence(ev)
                with st.expander("View raw API response"):
                    st.json(result)


# ---------- Evidence Viewer ----------
elif page == "🔎 Evidence Viewer":
    render_page_header(
        "WORKSPACE / EVIDENCE",
        "Evidence explorer",
        "Search source passages across the paper library and inspect their page, section and relevance metadata.",
    )
    with st.form("evidence_search_form"):
        query = st.text_input(
            "Search query",
            placeholder="e.g. small dataset limitation",
            help="Search for a concept, method, dataset or limitation mentioned in the papers.",
        )
        paper_id = st.text_input(
            "Limit to a paper ID (optional)",
            placeholder="Leave blank to search all papers",
        )
        top_k = st.slider("Maximum results", min_value=1, max_value=20, value=5)
        submitted = st.form_submit_button("Search evidence", type="primary", use_container_width=True)

    if submitted:
        if not query.strip():
            st.warning("Enter a search query first.")
        else:
            params = {"query": query.strip(), "top_k": top_k}
            if paper_id.strip():
                params["paper_id"] = paper_id.strip()
            with st.spinner("Searching the paper library..."):
                result, error = api_json("GET", "/evidence", params=params)
            if error:
                st.error(error)
            else:
                evidence = result.get("evidence", []) if isinstance(result, dict) else []
                st.session_state["last_evidence_result"] = evidence
                st.session_state["last_evidence_query"] = query.strip()

    evidence = st.session_state.get("last_evidence_result")
    previous_query = st.session_state.get("last_evidence_query")
    if evidence is not None:
        st.markdown(f"### {len(evidence)} result(s) for “{previous_query}”")
        if not evidence:
            st.info("No evidence found for this query.")
        else:
            for index, item in enumerate(evidence, start=1):
                title = item.get("paper_title") or item.get("paper_id") or "Unknown paper"
                with st.container(border=True):
                    st.markdown(f"**{index}. {title}**")
                    page = item.get("page", item.get("page_number", "?"))
                    section = item.get("section", "N/A")
                    score = item.get("relevance_score")
                    meta = [f"Section: {section}", f"Page {page}"]
                    if score is not None:
                        try:
                            meta.append(f"Relevance: {float(score):.2f}")
                        except (TypeError, ValueError):
                            meta.append(f"Relevance: {score}")
                    st.caption(" · ".join(meta))
                    st.write(item.get("text", "No evidence text returned."))

# ---------- Footer ----------
st.divider()
st.caption("SciInsight · Scientific Literature Intelligence · Existing backend response formats preserved.")

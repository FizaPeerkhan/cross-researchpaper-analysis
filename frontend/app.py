# frontend/app.py

import streamlit as st
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Scientific Literature Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .paper-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .gap-card {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff9800;
        margin-bottom: 1rem;
    }
    .evidence-box {
        background-color: #e8f5e9;
        padding: 0.75rem;
        border-radius: 0.25rem;
        border-left: 3px solid #4caf50;
        margin: 0.5rem 0;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔬 Scientific Literature Intelligence")
st.markdown("""
**Evidence-Grounded Information Extraction and Cross-Paper Research Gap Analysis**

Upload research papers, extract structured information, compare across papers, and identify candidate research gaps.
""")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to",
        ["📤 Upload Papers", "📄 Paper Explorer", "📊 Cross-Paper Analysis", "🔍 Research Gaps", "🔎 Evidence Viewer"],
    )
    
    st.divider()
    st.header("System Status")
    try:
        resp = requests.get(f"{API_URL}/")
        if resp.status_code == 200:
            st.success("API Connected")
        else:
            st.error("API Error")
    except:
        st.error("API Offline")


# ============ PAGE: UPLOAD PAPERS ============
if page == "📤 Upload Papers":
    st.header("Upload Research Papers")
    
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            with st.spinner(f"Uploading {uploaded_file.name}..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                resp = requests.post(f"{API_URL}/upload", files=files)
                
                if resp.status_code == 200:
                    result = resp.json()
                    st.success(f"✅ Uploaded: {uploaded_file.name} (ID: {result['paper_id']})")
                    
                    # Auto-extract
                    with st.spinner(f"Extracting information..."):
                        extract_resp = requests.post(f"{API_URL}/extract/{result['paper_id']}")
                        if extract_resp.status_code == 200:
                            st.info(f"✅ Extracted information from {uploaded_file.name}")
                        else:
                            st.warning(f"⚠️ Extraction failed for {uploaded_file.name}")
                else:
                    st.error(f"❌ Failed to upload {uploaded_file.name}")
    
    st.divider()
    st.subheader("Uploaded Papers")
    
    resp = requests.get(f"{API_URL}/papers")
    if resp.status_code == 200:
        papers = resp.json()["papers"]
        if papers:
            for paper in papers:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{paper.get('title', paper['filename'])}**")
                    st.caption(f"ID: {paper['paper_id']} | Uploaded: {paper['uploaded_at'][:19]}")
                with col2:
                    if paper["extracted"]:
                        st.success("Extracted")
                    else:
                        st.warning("Not extracted")
                with col3:
                    if not paper["extracted"]:
                        if st.button("Extract", key=f"extract_{paper['paper_id']}"):
                            with st.spinner("Extracting..."):
                                requests.post(f"{API_URL}/extract/{paper['paper_id']}")
                                st.rerun()
        else:
            st.info("No papers uploaded yet")


# ============ PAGE: PAPER EXPLORER ============
elif page == "📄 Paper Explorer":
    st.header("Paper Explorer")
    
    resp = requests.get(f"{API_URL}/papers")
    if resp.status_code == 200:
        papers = resp.json()["papers"]
        extracted_papers = [p for p in papers if p["extracted"]]
        
        if not extracted_papers:
            st.info("No extracted papers available. Upload and extract papers first.")
        else:
            selected = st.selectbox(
                "Select a paper",
                options=extracted_papers,
                format_func=lambda p: p.get("title", p["filename"]),
            )
            
            if selected:
                with st.spinner("Loading extraction..."):
                    ext_resp = requests.get(f"{API_URL}/extract/{selected['paper_id']}")
                    
                    if ext_resp.status_code == 200:
                        extraction = ext_resp.json()
                        
                        st.subheader(extraction["title"])
                        st.caption(f"Paper ID: {extraction['paper_id']}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### 🎯 Problem")
                            for item in extraction.get("problem", []):
                                st.write(f"• {item['value']}")
                            
                            st.markdown("### 🔧 Methods")
                            for item in extraction.get("methods", []):
                                with st.expander(f"**{item['value']}** (confidence: {item.get('confidence', 0):.2f})"):
                                    for ev in item.get("evidence", []):
                                        st.markdown(f'<div class="evidence-box">"{ev["text"]}"<br><small>Page {ev["page_number"]}</small></div>', unsafe_allow_html=True)
                            
                            st.markdown("### 📊 Datasets")
                            for item in extraction.get("datasets", []):
                                st.write(f"• {item['value']}")
                        
                        with col2:
                            st.markdown("### 📋 Tasks")
                            for item in extraction.get("tasks", []):
                                st.write(f"• {item['value']}")
                            
                            st.markdown("### 📈 Metrics")
                            for item in extraction.get("metrics", []):
                                st.write(f"• {item['value']}")
                            
                            st.markdown("### ⚠️ Limitations")
                            for item in extraction.get("limitations", []):
                                with st.expander(f"**{item['value'][:100]}...**"):
                                    for ev in item.get("evidence", []):
                                        st.markdown(f'<div class="evidence-box">"{ev["text"]}"<br><small>Page {ev["page_number"]}</small></div>', unsafe_allow_html=True)
                            
                            st.markdown("### 🔮 Future Work")
                            for item in extraction.get("future_work", []):
                                st.write(f"• {item['value'][:200]}")


# ============ PAGE: CROSS-PAPER ANALYSIS ============
elif page == "📊 Cross-Paper Analysis":
    st.header("Cross-Paper Analysis")
    
    resp = requests.get(f"{API_URL}/papers")
    if resp.status_code == 200:
        papers = resp.json()["papers"]
        extracted_papers = [p for p in papers if p["extracted"]]
        
        if len(extracted_papers) < 2:
            st.info("Need at least 2 extracted papers for comparison.")
        else:
            selected_ids = st.multiselect(
                "Select papers to compare",
                options=[p["paper_id"] for p in extracted_papers],
                format_func=lambda pid: next(
                    (p.get("title", p["filename"]) for p in extracted_papers if p["paper_id"] == pid),
                    pid,
                ),
                default=[p["paper_id"] for p in extracted_papers[:5]],
            )
            
            if st.button("🔍 Analyze", type="primary") and len(selected_ids) >= 2:
                with st.spinner("Analyzing papers..."):
                    resp = requests.post(f"{API_URL}/compare", json=selected_ids)
                    
                    if resp.status_code == 200:
                        result = resp.json()
                        
                        # Comparison results
                        st.subheader("📊 Common Methods")
                        common_methods = result["comparison"]["common_methods"]
                        if common_methods:
                            for method, papers in sorted(common_methods.items(), key=lambda x: -len(x[1])):
                                st.write(f"• **{method}** — used in {len(papers)} papers")
                        else:
                            st.info("No common methods found")
                        
                        st.subheader("📊 Common Datasets")
                        common_datasets = result["comparison"]["common_datasets"]
                        if common_datasets:
                            for dataset, papers in sorted(common_datasets.items(), key=lambda x: -len(x[1])):
                                st.write(f"• **{dataset}** — used in {len(papers)} papers")
                        else:
                            st.info("No common datasets found")
                        
                        st.subheader("⚠️ Common Limitations")
                        common_lims = result["comparison"]["common_limitations"]
                        if common_lims:
                            for lim_type, papers in sorted(common_lims.items(), key=lambda x: -len(x[1])):
                                st.write(f"• **{lim_type.replace('_', ' ').title()}** — {len(papers)} papers")
                        
                        # Trends
                        st.subheader("📈 Trends")
                        trends = result.get("trends", {})
                        
                        if trends.get("emerging_methods"):
                            st.markdown("**Emerging Methods:**")
                            for m in trends["emerging_methods"][:5]:
                                st.write(f"• {m['value']} ({m['frequency']:.0%})")
                        
                        # Visualizations
                        st.subheader("📊 Visualizations")
                        
                        import plotly.express as px
                        import pandas as pd
                        
                        # Method frequency chart
                        method_freq = trends.get("method_frequency", {})
                        if method_freq:
                            df = pd.DataFrame(
                                list(method_freq.items())[:10],
                                columns=["Method", "Count"],
                            )
                            fig = px.bar(df, x="Count", y="Method", orientation="h",
                                        title="Top Methods Across Papers")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Dataset frequency chart
                        dataset_freq = trends.get("dataset_frequency", {})
                        if dataset_freq:
                            df = pd.DataFrame(
                                list(dataset_freq.items())[:10],
                                columns=["Dataset", "Count"],
                            )
                            fig = px.bar(df, x="Count", y="Dataset", orientation="h",
                                        title="Top Datasets Across Papers")
                            st.plotly_chart(fig, use_container_width=True)


# ============ PAGE: RESEARCH GAPS ============
elif page == "🔍 Research Gaps":
    st.header("Research Gap Detection")
    
    st.markdown("""
    This module identifies **candidate research gaps** by analyzing patterns 
    across multiple papers. These are not proven gaps — they are directions 
    worth investigating.
    """)
    
    resp = requests.get(f"{API_URL}/papers")
    if resp.status_code == 200:
        papers = resp.json()["papers"]
        extracted_papers = [p for p in papers if p["extracted"]]
        
        if len(extracted_papers) < 2:
            st.info("Need at least 2 extracted papers for gap detection.")
        else:
            selected_ids = st.multiselect(
                "Select papers for gap analysis",
                options=[p["paper_id"] for p in extracted_papers],
                format_func=lambda pid: next(
                    (p.get("title", p["filename"]) for p in extracted_papers if p["paper_id"] == pid),
                    pid,
                ),
                default=[p["paper_id"] for p in extracted_papers[:5]],
            )
            
            if st.button("🔍 Detect Gaps", type="primary") and len(selected_ids) >= 2:
                with st.spinner("Analyzing for research gaps..."):
                    resp = requests.post(f"{API_URL}/gaps", json=selected_ids)
                    
                    if resp.status_code == 200:
                        result = resp.json()
                        
                        st.success(f"Analyzed {result['num_papers_analyzed']} papers")
                        st.caption(result.get("methodology_notes", ""))
                        
                        gaps = result.get("gaps", [])
                        
                        if not gaps:
                            st.info("No significant gaps detected.")
                        else:
                            st.subheader(f"🎯 {len(gaps)} Candidate Research Gaps")
                            
                            for i, gap in enumerate(gaps, 1):
                                confidence_color = {
                                    "high": "🟢",
                                    "medium": "🟡",
                                    "low": "🔴",
                                }.get(gap.get("confidence", "medium"), "⚪")
                                
                                with st.expander(
                                    f"{confidence_color} **Gap {i}: {gap['description'][:80]}...**"
                                ):
                                    col1, col2 = st.columns([2, 1])
                                    
                                    with col1:
                                        st.markdown(f"**Description:** {gap['description']}")
                                        st.markdown(f"**Type:** {gap['gap_type']}")
                                        st.markdown(f"**Confidence:** {gap['confidence']}")
                                        st.markdown(f"**Suggested Direction:** {gap['suggested_direction']}")
                                    
                                    with col2:
                                        st.markdown(f"**Supporting Papers:** {gap['frequency']}")
                                        st.markdown(f"**Related Limitations:** {', '.join(gap.get('related_limitations', []))}")
                                    
                                    if gap.get("evidence"):
                                        st.markdown("**Supporting Evidence:**")
                                        for ev in gap["evidence"]:
                                            st.markdown(
                                                f'<div class="evidence-box">'
                                                f'"{ev["text"][:300]}"'
                                                f'<br><small>Page {ev.get("page_number", "?")}</small>'
                                                f'</div>',
                                                unsafe_allow_html=True,
                                            )


# ============ PAGE: EVIDENCE VIEWER ============
elif page == "🔎 Evidence Viewer":
    st.header("Evidence Viewer")
    st.markdown("Search for evidence across all papers.")
    
    query = st.text_input("Enter your query", placeholder="e.g., small dataset limitation")
    paper_id = st.text_input("Paper ID (optional)", placeholder="Leave empty to search all papers")
    top_k = st.slider("Number of results", 1, 20, 5)
    
    if query:
        with st.spinner("Searching..."):
            params = {"query": query, "top_k": top_k}
            if paper_id:
                params["paper_id"] = paper_id
            
            resp = requests.get(f"{API_URL}/evidence", params=params)
            
            if resp.status_code == 200:
                evidence = resp.json()["evidence"]
                
                if not evidence:
                    st.info("No evidence found for this query.")
                else:
                    st.subheader(f"Found {len(evidence)} evidence snippets")
                    
                    for i, ev in enumerate(evidence, 1):
                        st.markdown(f"**{i}. {ev.get('paper_title', ev.get('paper_id', 'Unknown'))}**")
                        st.caption(f"Section: {ev.get('section', 'N/A')} | Page {ev.get('page', '?')} | Relevance: {ev.get('relevance_score', 0):.2f}")
                        st.markdown(f'<div class="evidence-box">"{ev["text"]}"</div>', unsafe_allow_html=True)
                        st.divider()
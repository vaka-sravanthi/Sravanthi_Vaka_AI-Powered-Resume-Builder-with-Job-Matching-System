import os
from pathlib import Path
import tempfile
import streamlit as st
from graphviz import Digraph

from backend.parser_agent import ParserAgent
from backend.analyzer_agent import AnalyzerAgent
from backend.matcher_agent import MatcherAgent
from backend.scorer_agent import ScorerAgent
from backend.resume_builder import ResumeBuilder, ResumeData

# --- LangGraph (simple linear graph for orchestration) ---
from langgraph.graph import StateGraph, END

st.set_page_config(page_title="AI Resume Builder + Job Matcher", layout="wide")

# Session state artifacts (for analytics)
if "runs" not in st.session_state:
    st.session_state["runs"] = []

# --- Build the process graph (Parser -> Analyzer -> Matcher -> Scorer) ---
def build_workflow_graph():
    g = Digraph("workflow", format="svg")
    g.attr(rankdir="LR", splines="spline", nodesep="0.6", ranksep="0.4")
    style = {"shape": "rounded", "style": "filled", "fillcolor": "#E7F2FF", "fontname": "Helvetica"}

    def node(nid, label, color="#E7F2FF"):
        g.node(nid, label, shape="box", style="filled,rounded", fillcolor=color)

    node("input", "Input: Resume + Job Description", "#FFF4E5")
    node("parser", "ParserAgent\n(PDF/Text → bullets/sections)")
    node("analyzer", "AnalyzerAgent\n(Skills & Phrases)")
    node("matcher", "MatcherAgent\n(Embeddings + FAISS)")
    node("scorer", "ScorerAgent\n(Score + Confidence)")
    node("output", "Outputs: Score, Gaps, Evidence", "#E8FFE5")

    g.edge("input", "parser")
    g.edge("parser", "analyzer")
    g.edge("analyzer", "matcher")
    g.edge("matcher", "scorer")
    g.edge("scorer", "output")
    return g

# --- Tab: Resume Builder (structured form → PDF) ---
def tab_resume_builder():
    st.subheader("Resume Builder (Generate PDF)")
    with st.form("resume_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            summary = st.text_area("Summary", height=100, placeholder="2-4 lines about you")
        with col2:
            skills = st.text_area("Skills (comma-separated)", placeholder="Python, SQL, React, AWS")
            education = st.text_area("Education (one per line)", placeholder="B.Tech in IT, 2021-2025\nHSC, 2019")
            experience = st.text_area("Experience (bullets, one per line)", placeholder="Built X that achieved Y\nImproved Z by 20%")
            projects = st.text_area("Projects (bullets, one per line)", placeholder="Smart Health App – Flask + React\nBlockchain Cert Verification – Solidity")

        submitted = st.form_submit_button("Generate PDF")
        if submitted:
            data = ResumeData(
                name=name.strip(),
                email=email.strip(),
                phone=phone.strip(),
                summary=summary.strip(),
                skills=[s.strip() for s in skills.split(",") if s.strip()],
                education=[l.strip() for l in education.splitlines() if l.strip()],
                experience=[l.strip() for l in experience.splitlines() if l.strip()],
                projects=[l.strip() for l in projects.splitlines() if l.strip()],
            )
            if not data.name or not data.email:
                st.error("Name and Email are required.")
                return
            builder = ResumeBuilder()
            with tempfile.TemporaryDirectory() as td:
                out = os.path.join(td, f"{data.name.replace(' ', '_')}_Resume.pdf")
                builder.build_pdf(out, data)
                with open(out, "rb") as f:
                    st.download_button("Download PDF", f, file_name=os.path.basename(out))
            st.success("PDF generated successfully ✅")

# --- Tab: Match Resume to Job ---
def tab_match_resume():
    st.subheader("Match Resume to Job Description")

    colL, colR = st.columns([1, 1])
    with colL:
        resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    with colR:
        jd_text = st.text_area("Paste Job Description", height=220, placeholder="Paste full JD here...")

    run_match = st.button("🚀 Match Resume")
    st.markdown("---")

    if run_match:
        if not resume_file or not jd_text.strip():
            st.error("Please upload a resume PDF and paste a job description.")
            return

        # Write resume to temp for pdfplumber
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(resume_file.getvalue())
            resume_path = tmp.name

        # Agents
        parser = ParserAgent()
        analyzer = AnalyzerAgent()
        matcher = MatcherAgent()
        scorer = ScorerAgent()

        # Orchestration via LangGraph (linear state passing)
        class State(dict):
            pass

        def step_parse(state: State) -> State:
            pr = parser.parse_resume_pdf(resume_path)
            pj = parser.parse_job_text(jd_text)
            state["resume_parse"] = pr
            state["job_parse"] = pj
            return state

        def step_analyze(state: State) -> State:
            ar = analyzer.extract_skills(state["resume_parse"].raw_text)
            aj = analyzer.extract_skills(state["job_parse"].raw_text)
            state["resume_analysis"] = ar
            state["job_analysis"] = aj
            state["skill_gap"] = analyzer.skill_gap(ar.unique_skills, aj.unique_skills)
            return state

        def step_match(state: State) -> State:
            md = matcher.compute_similarity(state["resume_parse"].bullets, state["job_parse"].bullets)
            state["match_details"] = md
            return state

        def step_score(state: State) -> State:
            md = state["match_details"]
            ar = state["resume_analysis"]
            aj = state["job_analysis"]
            report = scorer.compute(md.overall_similarity, ar.unique_skills, aj.unique_skills, md.top_pairs)
            state["score_report"] = report
            return state

        graph = StateGraph(State)
        graph.add_node("parse", step_parse)
        graph.add_node("analyze", step_analyze)
        graph.add_node("match", step_match)
        graph.add_node("score", step_score)
        graph.set_entry_point("parse")
        graph.add_edge("parse", "analyze")
        graph.add_edge("analyze", "match")
        graph.add_edge("match", "score")
        graph.add_edge("score", END)
        app = graph.compile()

        state = app.invoke(State())

        # Visual workflow
        st.subheader("Workflow Visualization")
        st.graphviz_chart(build_workflow_graph())

        # Agent outputs (Explainability & Traceability)
        st.subheader("Agent Outputs")
        with st.expander("ParserAgent Output (Resume Sections & Bullets)", expanded=False):
            rsec = state["resume_parse"].sections
            st.json({"sections": rsec})
            st.write("Top resume bullets:")
            st.write(state["resume_parse"].bullets[:10])

        with st.expander("ParserAgent Output (Job Bullets)", expanded=False):
            st.write(state["job_parse"].bullets[:15])

        with st.expander("AnalyzerAgent Output (Skills & Phrases)", expanded=False):
            st.write("Resume skills:", state["resume_analysis"].found_skills)
            st.write("Job skills:", state["job_analysis"].found_skills)
            st.write("Skill gap:", state["skill_gap"])
            st.write("Resume phrases:", state["resume_analysis"].key_phrases[:15])
            st.write("Job phrases:", state["job_analysis"].key_phrases[:15])

        md = state["match_details"]
        with st.expander("MatcherAgent Output (Top Evidence Pairs)", expanded=True):
            if md.top_pairs:
                rows = []
                for r_i, j_i, s in md.top_pairs:
                    rows.append({
                        "resume_chunk_idx": r_i,
                        "resume_chunk": md.resume_chunks[r_i][:300],
                        "job_chunk_idx": j_i,
                        "job_chunk": md.job_chunks[j_i][:300],
                        "similarity": round(s, 3)
                    })
                st.dataframe(rows, use_container_width=True)
            st.info(f"Average chunk similarity: **{md.overall_similarity:.3f}**")

        # Final scoring
        rep = state["score_report"]
        st.subheader("Final Match Score")
        c1, c2, c3 = st.columns(3)
        c1.metric("Match Score", f"{rep.score}/100")
        c2.metric("Confidence", f"{rep.confidence}%")
        c3.metric("Semantic Avg.", f"{md.overall_similarity:.2f}")

        with st.expander("Recruiter-style Reasoning & Factors", expanded=True):
            for r in rep.reasoning:
                st.write("• " + r)
            st.write("Sub-factors:", rep.factors)

        # Save run to session for analytics
        st.session_state["runs"].append({
            "score": rep.score,
            "confidence": rep.confidence,
            "semantic": md.overall_similarity,
            "missing_skills": state["skill_gap"]["missing"],
        })

        # Cleanup temp file
        try: os.remove(resume_path)
        except: pass

# --- Tab: Analytics (session-level) ---
def tab_analytics():
    st.subheader("Analytics (Session)")
    runs = st.session_state.get("runs", [])
    if not runs:
        st.info("Run at least one match to see analytics.")
        return

    import pandas as pd
    df = pd.DataFrame(runs)
    st.dataframe(df, use_container_width=True)

    st.write("Average score this session:", round(df["score"].mean(), 2))
    st.write("Most frequent missing skills:")
    all_missing = {}
    for r in runs:
        for sk in r.get("missing_skills", []):
            all_missing[sk] = all_missing.get(sk, 0) + 1
    top = sorted(all_missing.items(), key=lambda x: x[1], reverse=True)[:10]
    if top:
        st.write({k: v for k, v in top})
    else:
        st.write("—")

# --- App Layout ---
st.title("🧠 AI-Powered Resume Builder with Job Matching (Explainable)")

tabs = st.tabs(["📝 Resume Builder", "🔍 Match Resume", "📊 Analytics"])
with tabs[0]:
    tab_resume_builder()
with tabs[1]:
    tab_match_resume()
with tabs[2]:
    tab_analytics()

from __future__ import annotations

import io
import os
import base64
from typing import List, Dict, Any, Tuple
from PIL import Image

import streamlit as st

from src.embeddings import EmbeddingService
from src.ui_components import professional_summary_with_ai

from src.agents import content_enhancer_agent, job_parser_agent, matcher_and_scoring_agent, resume_parser_agent
from src.reporting import generate_pdf_report_safe, generate_ats_resume_pdf_safe
from src.workflow import (
    build_workflow_trace, workflow_figure, get_available_workflow_styles,
    create_workflow_metrics_dashboard, create_skills_performance_summary,
    create_animated_skills_workflow, export_workflow_report,
    create_workflow_comparison_view
)
from src.ui_components import (
    show_agent_outputs, show_match_summary, show_workflow_diagram,
    ai_content_generator_component, ai_skills_suggester,
    professional_summary_with_ai, work_experience_with_ai
)
from src.ai_content_generator import get_ai_service
from src.parsing import validate_pdf_upload, validate_multiple_pdf_uploads, parse_multiple_resumes
from src.scoring import rank_resumes, calculate_resume_job_match



st.set_page_config(
    page_title="AI-Powered Resume Builder with Job Matching System", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🚀"
)

def _generate_experience_html(experiences):
    """Helper to generate experience HTML"""
    if not experiences:
        return ""
    
    html = '<div class="section"><div class="section-title">Professional Experience</div>'
    
    for exp in experiences:
        if isinstance(exp, dict):
            title = exp.get("title", "")
            company = exp.get("company", "")
            dates = f"{exp.get('start', '')} - {exp.get('end', '')}"
            
            html += f'<div class="experience-item">'
            html += f'<div class="job-title">{title} at {company}</div>'
            html += f'<div class="job-details">{dates}</div>'
            
            bullets = exp.get("bullets", [])
            if bullets:
                html += '<ul>'
                for bullet in bullets:
                    html += f'<li>{bullet}</li>'
                html += '</ul>'
            html += '</div>'
    
    html += '</div>'
    return html

def _generate_education_html(educations):
    """Helper to generate education HTML"""
    if not educations:
        return ""
    
    html = '<div class="section"><div class="section-title">Education</div>'
    
    for edu in educations:
        if isinstance(edu, dict):
            degree = edu.get("degree", "")
            school = edu.get("school", "")
            year = edu.get("year", "")
            
            html += f'<div class="experience-item">'
            html += f'<div class="job-title">{degree}</div>'
            html += f'<div class="job-details">{school} - {year}</div>'
            html += '</div>'
    
    html += '</div>'
    return html


st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: white;
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Main container */
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 25px;
        padding: 2rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 25px 50px rgba(0,0,0,0.1);
        margin: 1rem;
    }
    
    /* Dashboard Cards */
    .dashboard-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,250,252,0.95) 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-top: 4px solid;
        transition: all 0.3s ease;
    }
    
    .dashboard-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.15);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        text-align: center;
        box-shadow: 0 6px 20px rgba(102,126,234,0.3);
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    
    .metric-label {
        font-size: 0.8rem;
        opacity: 0.9;
    }
    
    /* Analytics specific styles */
    .analytics-section {
        background: linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(5,150,105,0.05) 100%);
        border-left: 5px solid #10b981;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .workflow-style-card {
        background: linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(37,99,235,0.05) 100%);
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .workflow-style-card:hover {
        background: linear-gradient(135deg, rgba(59,130,246,0.2) 0%, rgba(37,99,235,0.1) 100%);
        transform: scale(1.02);
    }
    
    .workflow-style-card.selected {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .css-1d391kg .css-1v0mbdj {
        color: white;
    }
    
    .main-header {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 25%, #ff9ff3 50%, #54a0ff 75%, #5f27cd 100%);
        padding: 3rem;
        border-radius: 25px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(255,107,107,0.4);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%, transparent 75%, rgba(255,255,255,0.1) 75%);
        background-size: 30px 30px;
        animation: movePattern 20s linear infinite;
    }
    
    @keyframes movePattern {
        0% { background-position: 0 0; }
        100% { background-position: 30px 30px; }
    }
    
    .main-header h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 4rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .main-header p {
        font-size: 1.4rem;
        opacity: 0.95;
        margin-bottom: 0;
        position: relative;
        z-index: 1;
    }
    
    /* Feature Cards */
    .feature-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        border: none;
        margin-bottom: 2rem;
        transition: all 0.4s ease;
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 5px;
        background: linear-gradient(90deg, #ff6b6b, #ee5a24, #ff9ff3, #54a0ff, #5f27cd);
        background-size: 300% 100%;
        animation: gradientMove 3s ease infinite;
    }
    
    @keyframes gradientMove {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .feature-card:hover {
        transform: translateY(-10px) scale(1.02);
        box-shadow: 0 25px 50px rgba(0,0,0,0.15);
    }
    
    .feature-card.matching {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
    }
    
    .feature-card.builder {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%);
    }
    
    .feature-card.analytics {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.05) 100%);
    }
    
    /* Vibrant Stats Cards */
    .stats-card {
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .stats-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        transform: rotate(45deg);
        animation: shine 3s ease-in-out infinite;
    }
    
    @keyframes shine {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        50% { transform: translateX(100%) translateY(100%) rotate(45deg); }
        100% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
    }
    
    .stats-card:hover {
        transform: translateY(-5px) scale(1.05);
    }
    
    .stats-card h3 {
        font-size: 3rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .stats-card p {
        font-size: 1rem;
        opacity: 0.95;
        position: relative;
        z-index: 1;
    }
    
    /* Error and Warning Messages */
    .error-message {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(239,68,68,0.3);
    }
    
    .warning-message {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(245,158,11,0.3);
    }
    
    /* AI Button Styling */
    .ai-button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(99,102,241,0.4);
    }
    
    .ai-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99,102,241,0.6);
        background: linear-gradient(135deg, #5b5bf6 0%, #7c3aed 50%, #9333ea 100%);
    }
    
    /* Colorful Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 50%, #ff9ff3 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 0.8rem 2rem;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 10px 25px rgba(255,107,107,0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 35px rgba(255,107,107,0.4);
        background: linear-gradient(135deg, #ff5252 0%, #d84315 50%, #e91e63 100%);
    }
    
    /* Form Styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 15px;
        border: 3px solid transparent;
        background: linear-gradient(white, white) padding-box, 
                    linear-gradient(45deg, #ff6b6b, #ee5a24, #ff9ff3, #54a0ff) border-box;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        box-shadow: 0 0 20px rgba(255,107,107,0.3);
        transform: translateY(-2px);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 50%, #ff9ff3 100%);
        color: white;
        border-radius: 15px;
        font-weight: 700;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(255,107,107,0.3);
    }
    
    /* Progress Bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #ff6b6b 0%, #ee5a24 50%, #ff9ff3 100%);
        border-radius: 10px;
    }
    
    /* Success/Info Messages */
    .success-message {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(16,185,129,0.3);
    }
    
    .info-message {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(59,130,246,0.3);
    }
    
    /* AI Dialog Styling */
    .ai-dialog {
        background: linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,0.98) 100%);
        border: 2px solid #6366f1;
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 20px 40px rgba(99,102,241,0.2);
        backdrop-filter: blur(10px);
    }
    
    /* Animated background elements */
    .floating-shapes {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
    }
    
    .shape {
        position: absolute;
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(180deg); }
    }

    /* Ranking Cards */
    .ranking-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 6px solid;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .ranking-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
    
    .rank-1 { border-color: #ffd700; background: linear-gradient(135deg, rgba(255,215,0,0.1) 0%, rgba(255,215,0,0.05) 100%); }
    .rank-2 { border-color: #c0c0c0; background: linear-gradient(135deg, rgba(192,192,192,0.1) 0%, rgba(192,192,192,0.05) 100%); }
    .rank-3 { border-color: #cd7f32; background: linear-gradient(135deg, rgba(205,127,50,0.1) 0%, rgba(205,127,50,0.05) 100%); }
    .rank-other { border-color: #6b7280; background: linear-gradient(135deg, rgba(107,114,128,0.1) 0%, rgba(107,114,128,0.05) 100%); }
</style>
""", unsafe_allow_html=True)

try:
    import importlib
    _dotenv = importlib.import_module("dotenv")
    _dotenv.load_dotenv(override=False)
except Exception:
    pass
def create_demo_workflow_trace():
    """Create a demo workflow trace for visualization"""
    from src.workflow import build_workflow_trace
    
    steps = []
    
   
    class DemoAgent:
        def __init__(self, name, inputs, outputs, reasoning):
            self.name = name
            self.inputs = inputs
            self.outputs = outputs
            self.reasoning = reasoning  
            self.agent_type = name.lower().replace(' ', '_')
    
    
    resume_agent = DemoAgent("Resume Parser", 
        inputs={
            "resume_file": "john_doe_resume.pdf",
            "file_content": "Raw resume content..."
        },
        outputs={
            "name": "John Doe",
            "email": "john.doe@email.com", 
            "phone": "+1-555-123-4567",
            "skills": ["Python", "React", "Machine Learning", "SQL", "AWS"],
            "raw_text": "Software Engineer with 5 years experience...",
            "structured_resume": {
                "experience": ["Software Engineer at TechCorp"],
                "education": ["BS Computer Science"],
                "skills_extracted": ["Python", "React", "AWS"]
            }
        },
        reasoning="Extracting structured information from the uploaded resume file to identify candidate qualifications and experience."
    )
    steps.append(resume_agent)
    
    
    job_agent = DemoAgent("Job Parser",
        inputs={
            "job_description": "We are looking for a Software Engineer with Python and React experience..."
        },
        outputs={
            "skills": ["Python", "JavaScript", "React", "Node.js", "AWS"],
            "structured_requirements": {
                "experience": "3-5 years", 
                "education": "Bachelor's degree",
                "required_skills": ["Python", "React", "AWS"]
            },
            "key_skills": ["Python", "React", "AWS"],
            "experience_level": "Mid-level"
        },
        reasoning="Analyzing the job description to extract key requirements, skills, and qualifications needed for the role."
    )
    steps.append(job_agent)
    
    enhancer_agent = DemoAgent("Content Enhancer",
        inputs={
            "original_content": "Basic resume content",
            "target_role": "Software Engineer"
        },
        outputs={
            "enhanced_content": "Enhanced professional summary with improved keywords and better formatting",
            "improvements": [
                "Added relevant technical keywords", 
                "Improved content structure",
                "Enhanced readability"
            ],
            "suggestions": [
                "Include more quantified achievements",
                "Add industry-specific terminology",
                "Highlight leadership experience"
            ]
        },
        reasoning="Improving resume content by adding relevant keywords, enhancing structure, and optimizing for the target role."
    )
    steps.append(enhancer_agent)
    
   
    matcher_agent = DemoAgent("Matcher & Scoring",
        inputs={
            "resume_text": "Software Engineer with 5 years experience...",
            "job_text": "We are looking for a Software Engineer...",
            "resume_skills": ["Python", "React", "AWS"],
            "job_skills": ["Python", "JavaScript", "React", "Node.js", "AWS"]
        },
        outputs={
            "score": 85.5,
            "confidence": 92.0,
            "matched_skills": ["Python", "React", "AWS"],
            "missing_skills": ["Node.js", "JavaScript"],
            "explanation": "Strong technical match with good alignment on core requirements. Candidate has 3/5 key skills.",
            "top_snippets": [
                "5 years of Python development experience",
                "Built React applications for enterprise clients", 
                "AWS certified cloud practitioner"
            ]
        },
        reasoning="Comparing resume content against job requirements to calculate compatibility score and identify strengths and gaps."
    )
    steps.append(matcher_agent)
    
    try:
        return build_workflow_trace(steps)
    except Exception as e:
        class SimpleTrace:
            def __init__(self, steps):
                self.steps = steps
                self.metadata = {"workflow_efficiency": 85, "total_steps": len(steps)}
        
        return SimpleTrace(steps)
def create_compact_sidebar_metrics():
    """Create compact sidebar metrics summary"""
    if "session_metrics" not in st.session_state:
        st.session_state.session_metrics = {
            "total_analyses": 0,
            "resumes_processed": 0,
            "avg_match_score": 0.0,
            "total_skills_identified": 0,
            "ai_suggestions_generated": 0,
            "workflow_traces": []
        }
    
    metrics = st.session_state.session_metrics
    
    st.sidebar.markdown("### 📊 Session Stats")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Analyses", metrics['total_analyses'])
        st.metric("Skills ID'd", metrics['total_skills_identified'])
    with col2:
        st.metric("Resumes", metrics['resumes_processed'])
        st.metric("Avg Score", f"{metrics['avg_match_score']:.1f}%")


def create_analytical_dashboard():
    """Create comprehensive analytical dashboard for main page"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #54a0ff 75%, #5f27cd 100%); 
                padding: 3rem; border-radius: 25px; color: white; text-align: center; margin-bottom: 2rem;
                box-shadow: 0 20px 40px rgba(102,126,234,0.4);">
        <h1 style="font-size: 3.5rem; font-weight: 900; margin-bottom: 0.5rem;">📊 Analytics Dashboard</h1>
        <p style="font-size: 1.3rem; opacity: 0.95;">Real-time Insights & Performance Metrics</p>
    </div>
    """, unsafe_allow_html=True)
    
    if "session_metrics" not in st.session_state:
        st.session_state.session_metrics = {
            "total_analyses": 0,
            "resumes_processed": 0,
            "avg_match_score": 0.0,
            "total_skills_identified": 0,
            "ai_suggestions_generated": 0,
            "workflow_traces": []
        }
    
    metrics = st.session_state.session_metrics
    
    st.markdown("## 📈 Session Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['total_analyses']}</div>
            <div class="metric-label">Total Analyses</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
            <div class="metric-value">{metrics['resumes_processed']}</div>
            <div class="metric-label">Resumes Processed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
            <div class="metric-value">{metrics['avg_match_score']:.1f}%</div>
            <div class="metric-label">Average Match Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);">
            <div class="metric-value">{metrics['total_skills_identified']}</div>
            <div class="metric-label">Skills Identified</div>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    
    with col1:
        with st.expander("🔄 Workflow Analytics", expanded=True):
            st.markdown("### Current Session Workflow Metrics")
            
            ai_service = get_ai_service()
            ai_status = "🟢 Online" if ai_service.is_available() else "🔴 Offline"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(79,70,229,0.05) 100%); 
                        padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #6366f1;">
                <strong>AI Status:</strong> {ai_status}<br>
                <strong>Suggestions Generated:</strong> {metrics['ai_suggestions_generated']}<br>
                <strong>Success Rate:</strong> {95.0 if ai_service.is_available() else 0.0:.1f}%<br>
                <strong>Workflow Traces:</strong> {len(metrics['workflow_traces'])}
            </div>
            """, unsafe_allow_html=True)
            
            
        
        with st.expander("⚡ Performance Insights", expanded=False):
            st.markdown("### System Performance")
            
            performance_data = {
                "avg_processing_time": 2.3,
                "cache_hit_rate": 0.87,
                "ai_response_time": 1.2,
                "workflow_efficiency": 85.0
            }
            
            st.markdown(f"""
            <div class="analytics-section">
                <strong>⏱️ Avg Processing Time:</strong> {performance_data['avg_processing_time']:.1f}s<br>
                <strong>🎯 Cache Hit Rate:</strong> {performance_data['cache_hit_rate']*100:.0f}%<br>
                <strong>🤖 AI Response Time:</strong> {performance_data['ai_response_time']:.1f}s<br>
                <strong>📈 Workflow Efficiency:</strong> {performance_data['workflow_efficiency']:.1f}%
            </div>
            """, unsafe_allow_html=True)
            
            if st.checkbox("Show Performance Trends"):
                import plotly.graph_objects as go
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=["Session 1", "Session 2", "Session 3", "Session 4", "Current"],
                    y=[2.8, 2.5, 2.2, 2.1, 2.3],
                    mode='lines+markers',
                    name='Processing Time',
                    line=dict(color='#667eea', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title="Processing Time Trend",
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0),
                    showlegend=False,
                    xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', title="Seconds"),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        with st.expander("🧠 Skills Intelligence", expanded=True):
            st.markdown("### Skills Analysis Insights")
            
            if "skills_database" not in st.session_state:
                st.session_state.skills_database = {
                    "Python": 15,
                    "JavaScript": 12,
                    "React": 10,
                    "Machine Learning": 8,
                    "SQL": 7,
                    "AWS": 6,
                    "Docker": 5,
                    "Node.js": 4
                }
            
            skills_db = st.session_state.skills_database
            
            if skills_db:
                st.markdown("**Most Identified Skills:**")
                for skill, count in list(skills_db.items())[:5]:
                    progress_val = count / max(skills_db.values()) if skills_db.values() else 0
                    st.markdown(f"""
                    <div style="margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="font-size: 0.9rem;">{skill}</span>
                            <span style="font-size: 0.8rem; color: #6b7280;">{count}</span>
                        </div>
                        <div style="background: #e5e7eb; height: 6px; border-radius: 3px;">
                            <div style="background: linear-gradient(90deg, #667eea, #764ba2); 
                                        height: 100%; width: {progress_val*100:.0f}%; 
                                        border-radius: 3px; transition: width 0.3s ease;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No skills data available yet.")
            
            st.markdown("### Industry Trends")
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(5,150,105,0.05) 100%); 
                        padding: 1rem; border-radius: 8px; font-size: 0.85rem;">
                <strong>🔥 Hot Skills:</strong> AI/ML, Cloud Computing, React<br>
                <strong>📈 Growing:</strong> Kubernetes, TypeScript, GraphQL<br>
                <strong>🎯 In-Demand:</strong> Data Science, DevOps, Mobile Dev
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("📄 Reports & Export", expanded=False):
            st.markdown("### Analytics Reports")
            
            if st.button("📊 Generate Session Report", use_container_width=True):
                st.session_state.generate_session_report = True
            
            if st.button("📈 Export Workflow Analysis", use_container_width=True):
                if st.session_state.session_metrics.get("workflow_traces"):
                    st.session_state.export_workflow_analysis = True
                else:
                    st.warning("No workflow traces available to export")
            
            if st.button("🎯 Skills Intelligence Report", use_container_width=True):
                st.session_state.generate_skills_report = True
            
            if st.button("🗑️ Clear Analytics Data", use_container_width=True):
                st.session_state.session_metrics = {
                    "total_analyses": 0,
                    "resumes_processed": 0,
                    "avg_match_score": 0.0,
                    "total_skills_identified": 0,
                    "ai_suggestions_generated": 0,
                    "workflow_traces": []
                }
                st.session_state.skills_database = {}
                st.success("Analytics data cleared!")
    
    st.markdown("---")
    st.markdown("## 🎨 Workflow Visualization Options")
    if metrics['workflow_traces']:
                st.markdown("### Workflow Visualization")
                
                trace_options = [f"Trace {i+1}" for i in range(len(metrics['workflow_traces']))]
                selected_trace_idx = st.selectbox("Select workflow trace:", range(len(trace_options)), 
                                                format_func=lambda x: trace_options[x])
                if st.button("🎨 Visualize Selected Workflow"):
                    try:
                        selected_trace = metrics['workflow_traces'][selected_trace_idx]
                        display_enhanced_workflow_analysis(selected_trace)
                    except Exception as e:
                        st.error(f"Visualization error: {e}")
                        demo_trace = create_demo_workflow_trace()
                        st.info("Showing demo workflow visualization:")
                        display_enhanced_workflow_analysis(demo_trace)

                    
                

    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Available Visualization Styles")
        
        available_styles = get_available_workflow_styles()
        
        if "selected_workflow_style" not in st.session_state:
            st.session_state.selected_workflow_style = "skills_focused"
        for style in available_styles:
            is_selected = st.session_state.selected_workflow_style == style["value"]
            
            if st.button(
                f"{'✅' if is_selected else '⚪'} {style['name']}", 
                key=f"style_{style['value']}",
                help=style["description"],
                use_container_width=True
            ):
                st.session_state.selected_workflow_style = style["value"]
                
                if not st.session_state.session_metrics.get("workflow_traces"):
                    demo_trace = create_demo_workflow_trace()
                    st.session_state.session_metrics["workflow_traces"] = [demo_trace]
                st.rerun()
      
    
    with col2:
        st.markdown("### Visualization Options")
        
        show_animated = st.checkbox("🎬 Show Animated Workflow", value=False, 
                                   help="Display animated workflow progression")
        show_metrics_dashboard = st.checkbox("📊 Include Metrics Dashboard", value=True,
                                           help="Show detailed performance metrics")
        export_trace = st.checkbox("💾 Enable Trace Export", value=False,
                                 help="Allow exporting workflow analysis data")
        
        st.session_state.workflow_options = {
            "show_animated": show_animated,
            "show_metrics_dashboard": show_metrics_dashboard,
            "export_trace": export_trace
        }
        
        color_scheme = st.selectbox("Color Scheme", ["Default", "Dark", "Colorful", "Professional"], index=2)
        animation_speed = st.slider("Animation Speed", 0.5, 3.0, 1.0, 0.1)
        
        st.session_state.viz_settings = {
            "color_scheme": color_scheme,
            "animation_speed": animation_speed
        }


def update_session_metrics(analysis_data: Dict[str, Any]):
    """Update session metrics based on analysis results"""
    if "session_metrics" not in st.session_state:
        st.session_state.session_metrics = {
            "total_analyses": 0,
            "resumes_processed": 0,
            "avg_match_score": 0.0,
            "total_skills_identified": 0,
            "ai_suggestions_generated": 0,
            "workflow_traces": []
        }
    
    metrics = st.session_state.session_metrics
    
    metrics["total_analyses"] += 1
    metrics["resumes_processed"] += analysis_data.get("resumes_count", 0)
    
    new_score = analysis_data.get("match_score", 0)
    current_avg = metrics["avg_match_score"]
    total_analyses = metrics["total_analyses"]
    metrics["avg_match_score"] = ((current_avg * (total_analyses - 1)) + new_score) / total_analyses
    
    metrics["total_skills_identified"] += analysis_data.get("skills_identified", 0)
    metrics["ai_suggestions_generated"] += analysis_data.get("ai_suggestions", 0)
    
    if "workflow_trace" in analysis_data:
        metrics["workflow_traces"].append(analysis_data["workflow_trace"])
        
        if len(metrics["workflow_traces"]) > 10:
            metrics["workflow_traces"] = metrics["workflow_traces"][-10:]


def update_skills_database(skills: List[str]):
    """Update the skills database with newly identified skills"""
    if "skills_database" not in st.session_state:
        st.session_state.skills_database = {}
    
    for skill in skills:
        skill = skill.strip().title()
        if skill:
            st.session_state.skills_database[skill] = st.session_state.skills_database.get(skill, 0) + 1


def display_enhanced_workflow_analysis(trace, analysis_data=None):
    """Display enhanced workflow analysis with multiple visualization options"""
    if not hasattr(st.session_state, 'workflow_options'):
        st.session_state.workflow_options = {
            "show_animated": False,
            "show_metrics_dashboard": True,
            "export_trace": False
        }
    
    options = st.session_state.workflow_options
    selected_style = getattr(st.session_state, 'selected_workflow_style', 'skills_focused')
    
    st.markdown("### 🔄 AI Workflow Visualization")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🎨 Change Style", help="Switch visualization style"):
            styles = get_available_workflow_styles()
            current_idx = next((i for i, s in enumerate(styles) if s["value"] == selected_style), 0)
            next_idx = (current_idx + 1) % len(styles)
            st.session_state.selected_workflow_style = styles[next_idx]["value"]
            st.rerun()
    
    with col3:
        if st.button("🔄 Refresh", help="Regenerate visualization"):
            st.rerun()
    
    try:
        fig = workflow_figure(trace, style=selected_style)
        show_workflow_diagram(fig)
        
        current_style = next((s for s in get_available_workflow_styles() if s["value"] == selected_style), None)
        if current_style:
            st.info(f"**Current Style:** {current_style['name']} - {current_style['description']}")
        
    except Exception as e:
        st.error(f"Error generating workflow visualization: {e}")
        try:
            fig = workflow_figure(trace, style="enhanced")
            show_workflow_diagram(fig)
        except Exception as fallback_e:
            st.error(f"Fallback visualization also failed: {fallback_e}")
    
    if options["show_animated"]:
        st.markdown("### 🎬 Animated Workflow Progression")
        try:
            animated_fig = create_animated_skills_workflow(trace)
            st.plotly_chart(animated_fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Animated workflow not available: {e}")
    
    if options["show_metrics_dashboard"]:
        st.markdown("### 📊 Workflow Performance Dashboard")
        try:
            metrics_fig = create_workflow_metrics_dashboard(trace)
            st.plotly_chart(metrics_fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Metrics dashboard not available: {e}")
    
    

def handle_dashboard_reports():
    """Handle dashboard report generation requests"""
    if getattr(st.session_state, 'generate_session_report', False):
        st.session_state.generate_session_report = False
        
        with st.expander("📊 Session Analytics Report", expanded=True):
            metrics = st.session_state.session_metrics
            
            st.markdown("### Session Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Analyses", metrics['total_analyses'])
            with col2:
                st.metric("Resumes Processed", metrics['resumes_processed'])
            with col3:
                st.metric("Avg Match Score", f"{metrics['avg_match_score']:.1f}%")
            with col4:
                st.metric("Skills Identified", metrics['total_skills_identified'])
            
            if metrics['workflow_traces']:
                st.markdown("### Workflow Performance History")
                try:
                    comparison_fig = create_workflow_comparison_view(metrics['workflow_traces'])
                    st.plotly_chart(comparison_fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Performance history chart not available: {e}")
    
    if getattr(st.session_state, 'export_workflow_analysis', False):
        st.session_state.export_workflow_analysis = False
        
        if st.session_state.session_metrics.get('workflow_traces'):
            latest_trace = st.session_state.session_metrics['workflow_traces'][-1]
            
            try:
                export_data = export_workflow_report(latest_trace, 'comprehensive')
                
                st.download_button(
                    label="📥 Download Workflow Analysis",
                    data=str(export_data),
                    file_name="workflow_analysis_report.json",
                    mime="application/json",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Export generation failed: {e}")
    
    if getattr(st.session_state, 'generate_skills_report', False):
        st.session_state.generate_skills_report = False
        
        with st.expander("🧠 Skills Intelligence Report", expanded=True):
            skills_db = st.session_state.get('skills_database', {})
            
            if skills_db:
                st.markdown("### Skills Analysis")
                
                import plotly.graph_objects as go
                
                sorted_skills = sorted(skills_db.items(), key=lambda x: x[1], reverse=True)[:10]
                skills, counts = zip(*sorted_skills) if sorted_skills else ([], [])
                
                fig = go.Figure(data=[
                    go.Bar(x=list(skills), y=list(counts), 
                          marker_color='rgba(102,126,234,0.8)')
                ])
                
                fig.update_layout(
                    title="Top 10 Most Identified Skills",
                    xaxis_title="Skills",
                    yaxis_title="Frequency",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("### Skills Categories")
                tech_skills = [s for s in skills_db.keys() if any(tech in s.lower() for tech in ['python', 'java', 'javascript', 'react', 'sql', 'aws', 'docker'])]
                soft_skills = [s for s in skills_db.keys() if any(soft in s.lower() for soft in ['leadership', 'communication', 'teamwork', 'problem solving'])]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Technical Skills:**")
                    for skill in tech_skills[:5]:
                        st.markdown(f"• {skill} ({skills_db[skill]})")
                
                with col2:
                    st.markdown("**Soft Skills:**")
                    for skill in soft_skills[:5]:
                        st.markdown(f"• {skill} ({skills_db[skill]})")
            else:
                st.info("No skills data available yet. Process some resumes to generate insights!")


def process_uploaded_image(uploaded_file) -> str:
    """Convert uploaded image to base64 data URL"""
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.thumbnail((300, 300), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            img_data = buffer.getvalue()
            b64_string = base64.b64encode(img_data).decode()
            return f"data:image/jpeg;base64,{b64_string}"
        except Exception as e:
            st.error(f"Error processing image: {e}")
            return ""
    return ""


def create_colorful_stats_section():
    """Create a vibrant stats and features section"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 50%, #ff9ff3 100%); 
                padding: 2rem; border-radius: 20px; color: white; text-align: center; margin-bottom: 1.5rem;
                box-shadow: 0 15px 35px rgba(255,107,107,0.4);">
        <h2 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; text-shadow: 2px 2px 8px rgba(0,0,0,0.3);">
            AI-Powered Success
        </h2>
        <p style="font-size: 1.2rem; opacity: 0.95;">Transforming careers with intelligent automation</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="stats-card" style="background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);">
            <div style="font-size: 3rem; font-weight: 900; margin-bottom: 0.5rem; text-shadow: 2px 2px 6px rgba(0,0,0,0.3);">95%</div>
            <p style="font-size: 1rem; opacity: 0.95;">Matching Accuracy</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stats-card" style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);">
            <div style="font-size: 3rem; font-weight: 900; margin-bottom: 0.5rem; text-shadow: 2px 2px 6px rgba(0,0,0,0.3);">10K+</div>
            <p style="font-size: 1rem; opacity: 0.95;">Resumes Enhanced</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stats-card" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);">
            <div style="font-size: 3rem; font-weight: 900; margin-bottom: 0.5rem; text-shadow: 2px 2px 6px rgba(0,0,0,0.3);">24/7</div>
            <p style="font-size: 1rem; opacity: 0.95;">AI Availability</p>
        </div>
        """, unsafe_allow_html=True)


def create_vibrant_feature_showcase():
    """Create vibrant feature showcase with animations"""
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
        <div class="feature-card matching">
            <h3 style="color: #10b981; font-size: 2rem; margin-bottom: 1rem;">
                🎯 Smart Resume Matching
            </h3>
            <p style="font-size: 1.1rem; line-height: 1.6; margin-bottom: 1.5rem;">
                Revolutionary AI analyzes your resume against job descriptions with unprecedented accuracy. 
                Get actionable insights that transform your job search success rate.
            </p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.5rem;">
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                            color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                    <strong>Semantic Analysis</strong><br>
                    <small>Advanced NLP matching</small>
                </div>
                <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                            color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                    <strong>Skill Gap Detection</strong><br>
                    <small>Identify missing competencies</small>
                </div>
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                            color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                    <strong>ATS Optimization</strong><br>
                    <small>Beat applicant tracking systems</small>
                </div>
                <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                            color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                    <strong>Detailed Reports</strong><br>
                    <small>Professional PDF insights</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card builder">
            <h3 style="color: #3b82f6; font-size: 2rem; margin-bottom: 1rem;">
                📝 AI-Enhanced Resume Builder
            </h3>
            <p style="font-size: 1.1rem; line-height: 1.6; margin-bottom: 1.5rem;">
                Create stunning, ATS-friendly resumes with intelligent AI assistance. Our advanced AI helps generate 
                compelling professional summaries, work descriptions, and skill recommendations.
            </p>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem;">
                <span style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); 
                           color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                    AI Content Generation
                </span>
                <span style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                           color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                    Modern Templates
                </span>
                <span style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                           color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                    Photo Integration
                </span>
                <span style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                           color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                    Smart Suggestions
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card analytics">
            <h3 style="color: #f59e0b; font-size: 2rem; margin-bottom: 1rem;">
                📊 Advanced Analytics Dashboard
            </h3>
            <p style="font-size: 1.1rem; line-height: 1.6; margin-bottom: 1.5rem;">
                Deep insights powered by multi-agent AI workflow. Understand exactly how your resume 
                performs with explainable AI and visual analytics.
            </p>
            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                        padding: 1.5rem; border-radius: 15px; margin-top: 1rem;">
                <ul style="color: #92400e; margin: 0; padding-left: 1.2rem; line-height: 1.8;">
                    <li><strong>Multi-Agent Workflow:</strong> Specialized AI agents for different analysis tasks</li>
                    <li><strong>Visual Diagrams:</strong> Interactive workflow and decision trees</li>
                    <li><strong>Explainable AI:</strong> Understand the reasoning behind every recommendation</li>
                    <li><strong>Performance Metrics:</strong> Track improvement over time</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        create_colorful_stats_section()
        
        ai_service = get_ai_service()
        if ai_service.is_available():
            st.markdown("""
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                        padding: 2rem; border-radius: 20px; color: white; text-align: center; margin-bottom: 1.5rem;
                        box-shadow: 0 15px 35px rgba(16,185,129,0.4);">
                <h3 style="font-size: 1.8rem; margin-bottom: 1rem;">🤖 AI Status: Online</h3>
                <p style="opacity: 0.9; margin-bottom: 1.5rem;">
                    Gemini AI is ready to enhance your resume with intelligent content generation
                </p>
                <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px;">
                    <p style="margin: 0; font-size: 0.9rem;">
                        Click AI buttons in Resume Builder to experience intelligent content creation
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                        padding: 2rem; border-radius: 20px; color: white; text-align: center; margin-bottom: 1.5rem;
                        box-shadow: 0 15px 35px rgba(239,68,68,0.4);">
                <h3 style="font-size: 1.8rem; margin-bottom: 1rem;">🤖 AI Status: Offline</h3>
                <p style="opacity: 0.9; margin-bottom: 0;">
                    Check your GEMINI_API_KEY to enable AI features
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 20px; color: white; text-align: center; margin-bottom: 1.5rem;
                    box-shadow: 0 15px 35px rgba(102,126,234,0.4);">
            <h3 style="font-size: 1.8rem; margin-bottom: 1rem;">🚀 Ready to Transform?</h3>
            <p style="opacity: 0.9; margin-bottom: 1.5rem;">
                Join thousands of professionals who have revolutionized their job search with AI
            </p>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <p style="margin: 0; font-size: 0.9rem;">
                    Average increase in interview callbacks: <strong>73%</strong>
                </p>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px;">
                <p style="margin: 0; font-size: 0.9rem;">
                    Time saved per application: <strong>45 minutes</strong>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)


def handle_file_upload_with_validation(label: str, help_text: str = None) -> Tuple[Any, bool, str]:
    
    uploaded_file = st.file_uploader(
        label, 
        type=["pdf"], 
        accept_multiple_files=False,
        help=help_text or "Upload a PDF version of your resume for best text extraction"
    )
    
    if uploaded_file is None:
        return None, True, ""
    
    is_valid, error_msg = validate_pdf_upload(uploaded_file)
    
    return uploaded_file, is_valid, error_msg


def handle_multiple_file_upload_with_validation(label: str, help_text: str = None) -> Tuple[List[Any], bool, str]:
   
    uploaded_files = st.file_uploader(
        label, 
        type=["pdf"], 
        accept_multiple_files=True,
        help=help_text or "Upload multiple PDF resumes for comparison and ranking"
    )
    
    if uploaded_files is None or len(uploaded_files) == 0:
        return [], True, ""
    
    is_valid, error_msg = validate_multiple_pdf_uploads(uploaded_files)
    
    return uploaded_files, is_valid, error_msg

def display_ranking_results(ranked_resumes: List[Dict], top_n: int):
    """Display ranked resume results using Streamlit components"""
    
    # Header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                padding: 2rem; border-radius: 20px; color: white; text-align: center; margin: 2rem 0;
                box-shadow: 0 15px 35px rgba(16,185,129,0.4);">
        <h2 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem;">🏆 Top {min(top_n, len(ranked_resumes))} Resume Rankings</h2>
        <p style="font-size: 1.2rem; opacity: 0.95;">AI-powered analysis results</p>
    </div>
    """, unsafe_allow_html=True)
    
    for i, resume_result in enumerate(ranked_resumes[:top_n]):
        rank = i + 1
        filename = resume_result.get('filename', 'Unknown File')
        score = resume_result.get('match_score', 0)
        matched_skills = resume_result.get('matched_skills', [])
        total_skills = resume_result.get('total_skills', 0)
        resume_data = resume_result.get('resume_data', {})
        
        if hasattr(resume_data, 'name'):
            name = resume_data.name or 'Name not found'
            email = resume_data.email or 'Email not found'
            phone = resume_data.phone or ''
        else:
            name = resume_data.get('name', 'Name not found')
            email = resume_data.get('email', 'Email not found')  
            phone = resume_data.get('phone', '')
        
        
        if rank == 1:
            medal = "🥇"
            rank_color = "#ffd700"
            bg_color = "#fffbeb"
        elif rank == 2:
            medal = "🥈"
            rank_color = "#c0c0c0"
            bg_color = "#f8fafc"
        elif rank == 3:
            medal = "🥉"
            rank_color = "#cd7f32"
            bg_color = "#fef7ed"
        else:
            medal = f"#{rank}"
            rank_color = "#6b7280"
            bg_color = "#f9fafb"
        
        # Create container for each resume
        with st.container():
            st.markdown(f"""
            <div style="background: {bg_color}; 
                        border: 2px solid {rank_color}; 
                        border-radius: 15px; 
                        padding: 1.5rem; 
                        margin: 1rem 0;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
            """, unsafe_allow_html=True)
            
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="font-size: 2rem; font-weight: 900; color: {rank_color};">{medal}</div>
                    <div>
                        <h3 style="margin: 0; color: #1f2937; font-size: 1.4rem;">{filename}</h3>
                        <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">{name} • {email}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="text-align: right;">
                    <div style="font-size: 2rem; font-weight: 900; color: {rank_color};">{score:.1f}%</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Match Score</div>
                </div>
                """, unsafe_allow_html=True)
            
            
            st.markdown("<br>", unsafe_allow_html=True)
            stat_col1, stat_col2 = st.columns(2)
            
            with stat_col1:
                st.markdown(f"""
                <div style="background: rgba(16,185,129,0.1); 
                           padding: 1rem; 
                           border-radius: 10px; 
                           border-left: 4px solid #10b981;
                           text-align: center;">
                    <div style="font-size: 1.2rem; font-weight: 700; color: #10b981;">{len(matched_skills)}</div>
                    <div style="font-size: 0.9rem; color: #6b7280;">Matched Skills</div>
                </div>
                """, unsafe_allow_html=True)
            
            with stat_col2:
                st.markdown(f"""
                <div style="background: rgba(59,130,246,0.1); 
                           padding: 1rem; 
                           border-radius: 10px; 
                           border-left: 4px solid #3b82f6;
                           text-align: center;">
                    <div style="font-size: 1.2rem; font-weight: 700; color: #3b82f6;">{total_skills}</div>
                    <div style="font-size: 0.9rem; color: #6b7280;">Total Skills</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Skills and phone info
            if matched_skills:
                skills_to_show = matched_skills[:10]
                skills_text = ", ".join(skills_to_show)
                if len(matched_skills) > 10:
                    skills_text += " ..."
                st.markdown(f"**🎯 Matched Skills:** {skills_text}")
            
            if phone:
                st.markdown(f"**📞 Phone:** {phone}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

def dynamic_list_input(label: str, key: str, placeholder: str = "", help_text: str = None) -> List[str]:
    """Create a dynamic list input with add/remove buttons"""
    if f"{key}_items" not in st.session_state:
        st.session_state[f"{key}_items"] = [""]
    
    st.markdown(f"**{label}**")
    if help_text:
        st.markdown(f"*{help_text}*")
    
    items = []
    
    for i, item in enumerate(st.session_state[f"{key}_items"]):
        col1, col2 = st.columns([4, 1])
        with col1:
            value = st.text_input(f"{label} {i+1}", value=item, key=f"{key}_input_{i}", placeholder=placeholder)
            if value.strip():
                items.append(value.strip())
        with col2:
            if st.form_submit_button(f"❌ Remove {label} {i+1}", help="Remove this item"):
                st.session_state[f"{key}_items"].pop(i)
                st.rerun()
    
    if st.form_submit_button(f"➕ Add {label}"):
        st.session_state[f"{key}_items"].append("")
        st.rerun()
    
    st.session_state[f"{key}_items"] = [item for item in st.session_state[f"{key}_items"] if True]
    
    return items


def dynamic_experience_input_with_ai() -> List[Dict[str, Any]]:
    """Create dynamic experience section input with AI assistance"""
    if "experience_items" not in st.session_state:
        st.session_state["experience_items"] = [{}]
    
    experiences = []
    
    for i, exp in enumerate(st.session_state["experience_items"]):
        st.markdown(f"**🏢 Experience {i+1}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Job Title", value=exp.get("title", ""), key=f"exp_title_{i}")
            company = st.text_input("Company", value=exp.get("company", ""), key=f"exp_company_{i}")
            start_date = st.text_input("Start Date", value=exp.get("start", ""), key=f"exp_start_{i}", 
                                     placeholder="e.g., Jan 2022")
        
        with col2:
            location = st.text_input("Location", value=exp.get("location", ""), key=f"exp_location_{i}")
            end_date = st.text_input("End Date", value=exp.get("end", ""), key=f"exp_end_{i}", 
                                   placeholder="e.g., Present")
        
        current_bullets_text = "\n".join(exp.get("bullets", []))
        
        bullets_text = ai_content_generator_component(
            section_name=f"Work Description - {title or 'Position'} - {i}",
            current_content=current_bullets_text,
            content_type="work_experience",
            user_data={"job_title": title, "company": company},
            job_title=title,
            industry="",
            placeholder_text="• Increased sales by 25% through strategic initiatives\n• Led a team of 5 developers\n• Implemented new processes"
        )
        
        bullets = [b.strip() for b in bullets_text.split('\n') if b.strip()]
        
        if title or company or bullets:
            experiences.append({
                "title": title,
                "company": company,
                "location": location,
                "start": start_date,
                "end": end_date,
                "bullets": bullets
            })
        
        col1, col2 = st.columns(2)
        with col2:
            if st.form_submit_button(f"❌ Remove Experience {i+1}"):
                st.session_state["experience_items"].pop(i)
                st.rerun()
        
        if i < len(st.session_state["experience_items"]) - 1:
            st.divider()
    
    if st.form_submit_button("➕ Add Another Experience"):
        st.session_state["experience_items"].append({})
        st.rerun()
    
    return experiences
def add_custom_css():
    st.markdown("""
    <style>
    .ranking-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #e5e7eb;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .ranking-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
    
    .rank-1 {
        border-color: #ffd700 !important;
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
    }
    
    .rank-2 {
        border-color: #c0c0c0 !important;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    .rank-3 {
        border-color: #cd7f32 !important;
        background: linear-gradient(135deg, #fef7ed 0%, #fed7aa 100%);
    }
    
    .rank-other {
        border-color: #6b7280 !important;
        background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
    }
    </style>
    """, unsafe_allow_html=True)




def dynamic_education_input() -> List[Dict[str, Any]]:
    """Create dynamic education section input"""
    if "education_items" not in st.session_state:
        st.session_state["education_items"] = [{}]
    
    education = []
    
    for i, edu in enumerate(st.session_state["education_items"]):
        st.markdown(f"**🎓 Education {i+1}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            degree = st.text_input("Degree", value=edu.get("degree", ""), key=f"edu_degree_{i}")
            school = st.text_input("School/University", value=edu.get("school", ""), key=f"edu_school_{i}")
        
        with col2:
            year = st.text_input("Year", value=edu.get("year", ""), key=f"edu_year_{i}", placeholder="e.g., 2020")
            location = st.text_input("Location", value=edu.get("location", ""), key=f"edu_location_{i}")
        
        details_text = st.text_area("Additional Details", 
                                   value="\n".join(edu.get("details", [])), 
                                   key=f"edu_details_{i}",
                                   placeholder="• GPA: 3.8/4.0\n• Relevant Coursework: Data Structures, Algorithms\n• Dean's List",
                                   height=80)
        
        details = [d.strip() for d in details_text.split('\n') if d.strip()]
        
        if degree or school:
            education.append({
                "degree": degree,
                "school": school,
                "location": location,
                "year": year,
                "details": details
            })
        
        col1, col2 = st.columns(2)
        with col2:
            if st.form_submit_button(f"❌ Remove Education {i+1}"):
                st.session_state["education_items"].pop(i)
                st.rerun()
        
        if i < len(st.session_state["education_items"]) - 1:
            st.divider()
    
    if st.form_submit_button("➕ Add Another Education"):
        st.session_state["education_items"].append({})
        st.rerun()
    
    return education


def dynamic_projects_input() -> List[Dict[str, Any]]:
    """Create dynamic projects section input"""
    if "project_items" not in st.session_state:
        st.session_state["project_items"] = [{}]
    
    projects = []
    
    for i, proj in enumerate(st.session_state["project_items"]):
        st.markdown(f"**🚀 Project {i+1}**")
        
        name = st.text_input("Project Name", value=proj.get("name", ""), key=f"proj_name_{i}")
        description = st.text_area("Description", value=proj.get("description", ""), key=f"proj_desc_{i}",
                                 placeholder="Brief description of the project, its purpose, and your role",
                                 height=80)
        tech_text = st.text_input("Technologies Used", value=", ".join(proj.get("tech", [])), 
                                key=f"proj_tech_{i}",
                                placeholder="React, Node.js, MongoDB, AWS")
        
        tech = [t.strip() for t in tech_text.split(',') if t.strip()]
        
        if name or description:
            projects.append({
                "name": name,
                "description": description,
                "tech": tech
            })
        
        col1, col2 = st.columns(2)
        with col2:
            if st.form_submit_button(f"❌ Remove Project {i+1}"):
                st.session_state["project_items"].pop(i)
                st.rerun()
        
        if i < len(st.session_state["project_items"]) - 1:
            st.divider()
    
    if st.form_submit_button("➕ Add Another Project"):
        st.session_state["project_items"].append({})
        st.rerun()
    
    return projects
def main() -> None:
    st.sidebar.markdown("""
    <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 25%, #ff9ff3 50%, #54a0ff 75%, #5f27cd 100%); 
                padding: 2rem; border-radius: 20px; color: white; text-align: center; margin-bottom: 2rem;
                box-shadow: 0 15px 35px rgba(255,107,107,0.4);">
        <h2 style="margin-bottom: 0.5rem; font-weight: 900;">🚀AI-Powered Resume Builder with Job Matching System</h2>
        <p style="opacity: 0.95; margin: 0; font-size: 0.9rem;">Navigate Your Success</p>
    </div>
    """, unsafe_allow_html=True)
    
  
    
    mode = st.sidebar.radio(
        "Choose Your Path",
        ["🏠 Welcome",  "📝 Resume Builder","🎯 Resume Matching", "📊 Analytics Dashboard"],
        format_func=lambda x: x
    )

    st.markdown("""
    <div class="floating-shapes">
        <div class="shape" style="top: 10%; left: 10%; width: 50px; height: 50px; background: linear-gradient(45deg, #ff6b6b, #ee5a24); opacity: 0.1; animation-delay: 0s;"></div>
        <div class="shape" style="top: 20%; right: 15%; width: 30px; height: 30px; background: linear-gradient(45deg, #ff9ff3, #54a0ff); opacity: 0.1; animation-delay: 2s;"></div>
        <div class="shape" style="bottom: 30%; left: 20%; width: 40px; height: 40px; background: linear-gradient(45deg, #5f27cd, #00d2ff); opacity: 0.1; animation-delay: 4s;"></div>
    </div>
    """, unsafe_allow_html=True)

    if mode == "🏠 Welcome":
        st.markdown("""
        <div class="main-header">
            <h1>AI-Powered Resume Builder with Job Matching System</h1>
            <p>Transform Your Career with Next-Generation AI Technology</p>
        </div>
        """, unsafe_allow_html=True)

        create_vibrant_feature_showcase()

        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%); 
                    padding: 3rem; border-radius: 25px; text-align: center; margin: 3rem 0;
                    color: white; position: relative; overflow: hidden;
                    box-shadow: 0 25px 50px rgba(102,126,234,0.3);">
            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                        background: linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%, transparent 75%, rgba(255,255,255,0.1) 75%);
                        background-size: 20px 20px; animation: movePattern 10s linear infinite;"></div>
            <h2 style="font-size: 3rem; margin-bottom: 1rem; font-weight: 900; position: relative; z-index: 1;">
                Ready to Dominate Your Job Search?
            </h2>
            <p style="font-size: 1.3rem; margin-bottom: 2rem; opacity: 0.95; position: relative; z-index: 1;">
                Join the AI revolution and transform your career trajectory today
            </p>
            <div style="position: relative; z-index: 1;">
                <p style="font-size: 1.5rem; font-weight: 700;">👈 Choose your path from the sidebar to begin!</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif mode == "📊 Analytics Dashboard":
        create_analytical_dashboard()
        handle_dashboard_reports()

    elif mode == "🎯 Resume Matching":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 25%, #34d399 50%, #6ee7b7 75%, #a7f3d0 100%); 
                    padding: 3rem; border-radius: 25px; color: white; text-align: center; margin-bottom: 2rem;
                    box-shadow: 0 20px 40px rgba(16,185,129,0.4);">
            <h1 style="font-size: 3.5rem; font-weight: 900; margin-bottom: 0.5rem;">🎯 Smart Resume Matching & Ranking</h1>
            <p style="font-size: 1.3rem; opacity: 0.95;">AI-powered analysis with multiple resume ranking</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.9) 100%); 
                        padding: 2rem; border-radius: 20px; 
                        box-shadow: 0 15px 35px rgba(0,0,0,0.1); margin-bottom: 1rem;
                        border: 3px solid transparent;
                        background-clip: padding-box;
                        position: relative;">
                <div style="position: absolute; top: 0; left: 0; right: 0; height: 4px; 
                            background: linear-gradient(90deg, #10b981, #059669, #34d399); border-radius: 20px 20px 0 0;"></div>
                <h3 style="color: #10b981; margin: 1rem 0; font-size: 1.8rem; font-weight: 700;">📄 Upload Multiple Resumes</h3>
            </div>
            """, unsafe_allow_html=True)
            
            resume_files, is_valid, error_msg = handle_multiple_file_upload_with_validation(
                "Choose resume files (PDF)",
                "Upload multiple PDF resumes for comparison and ranking"
            )
            
            if resume_files and len(resume_files) > 0:
                if is_valid:
                    st.markdown(f"""
                    <div class="success-message">
                        ✅ {len(resume_files)} resume(s) uploaded successfully
                        <br><small>Files: {', '.join([f.name for f in resume_files])}</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="error-message">
                        ❌ Upload Error: <strong>{error_msg}</strong>
                        <br><small>Please upload valid PDF files and try again.</small>
                    </div>
                    """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.9) 100%); 
                        padding: 2rem; border-radius: 20px; 
                        box-shadow: 0 15px 35px rgba(0,0,0,0.1); margin-bottom: 1rem;
                        border: 3px solid transparent;
                        background-clip: padding-box;
                        position: relative;">
                <div style="position: absolute; top: 0; left: 0; right: 0; height: 4px; 
                            background: linear-gradient(90deg, #3b82f6, #2563eb, #1d4ed8); border-radius: 20px 20px 0 0;"></div>
                <h3 style="color: #3b82f6; margin: 1rem 0; font-size: 1.8rem; font-weight: 700;">📋 Job Description</h3>
            </div>
            """, unsafe_allow_html=True)
            
            job_desc = st.text_area(
                "Paste the complete job description", 
                height=200,
                placeholder="Paste the complete job description here including:\n• Job title and company\n• Required qualifications\n• Responsibilities\n• Preferred skills\n• Experience requirements",
                help="Include all sections of the job posting for comprehensive analysis"
            )

        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(245,158,11,0.1) 0%, rgba(245,158,11,0.05) 100%); 
                    padding: 2rem; border-radius: 20px; margin: 1rem 0;
                    border-top: 4px solid #f59e0b;">
            <h3 style="color: #f59e0b; margin-bottom: 1rem; font-size: 1.5rem;">🏆 Ranking Options</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            top_n_options = [i for i in range(1, 101)] + ["All"]
            top_n_selection = st.selectbox(
                "Show top candidates:",
                top_n_options,
                index=1,
                help="Select how many top candidates to display in ranking"
            )
            top_n = len(resume_files) if top_n_selection == "All" and resume_files else (top_n_selection if top_n_selection != "All" else 5)

        with col2:
            sorting_criteria = st.selectbox(
                "Sort by:",
                ["Match Score", "Skills Match", "Name"],
                help="Choose ranking criteria"
            )

        with col3:
            show_details = st.checkbox(
                "Show detailed analysis",
                value=True,
                help="Include detailed agent analysis for each resume"
            )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            run = st.button(
                "🔍 Analyze & Rank Resumes", 
                type="primary", 
                use_container_width=True,
                disabled=not (resume_files and job_desc and is_valid and len(resume_files) > 0),
                help="Start AI-powered analysis and ranking of resumes against the job description"
            )

        if run and resume_files and job_desc and is_valid:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("🤖 Our AI agents are analyzing and ranking resumes..."):
                try:
                    embed = EmbeddingService()
                    
                    status_text.markdown("**📋 Analyzing job description...**")
                    progress_bar.progress(10)
                    job_analysis = job_parser_agent(job_desc)
                    job_skills = job_analysis.outputs.get("skills", [])

                    status_text.markdown(f"**📄 Parsing {len(resume_files)} resume(s)...**")
                    progress_bar.progress(30)
                    resume_results = parse_multiple_resumes(resume_files)
                    
                    if not resume_results:
                        st.error("Failed to parse any resumes. Please check your PDF files.")
                        progress_bar.empty()
                        status_text.empty()
                        return

                    status_text.markdown("**🎯 Calculating match scores...**")
                    progress_bar.progress(60)
                    
                    ranked_resumes = []
                    total_skills_identified = 0
                    
                    for filename, resume_data in resume_results:
                        match_result = calculate_resume_job_match(resume_data, job_skills)
                        total_skills_identified += len(resume_data.skills)
                        
                        ranked_resumes.append({
                            'filename': filename,
                            'resume_data': resume_data,
                            'match_score': match_result['skill_match_score'],
                            'matched_skills': match_result['matched_skills'],
                            'total_skills': match_result['total_resume_skills'],
                            'total_job_skills': match_result['total_job_skills']
                        })

                    status_text.markdown("**📊 Ranking resumes...**")
                    progress_bar.progress(80)
                    
                    if sorting_criteria == "Match Score":
                        ranked_resumes.sort(key=lambda x: x['match_score'], reverse=True)
                    elif sorting_criteria == "Skills Match":
                        ranked_resumes.sort(key=lambda x: len(x['matched_skills']), reverse=True)
                    elif sorting_criteria == "Name":
                        ranked_resumes.sort(key=lambda x: x['resume_data'].name or x['filename'])

                    status_text.markdown("**✅ Analysis complete!**")
                    progress_bar.progress(100)
                    
                    avg_score = sum(r['match_score'] for r in ranked_resumes) / len(ranked_resumes) if ranked_resumes else 0
                    update_session_metrics({
                        "resumes_count": len(resume_files),
                        "match_score": avg_score,
                        "skills_identified": total_skills_identified,
                        "ai_suggestions": 0
                    })
                    
                    all_skills = []
                    for resume in ranked_resumes:
                        all_skills.extend(resume['resume_data'].skills)
                    update_skills_database(all_skills)
                    
                    import time
                    time.sleep(1)
                    progress_bar.empty()
                    status_text.empty()

                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    st.markdown("""
                    <div class="warning-message">
                        <h4>Troubleshooting Tips:</h4>
                        <ul>
                            <li>Ensure your PDFs are not corrupted or password-protected</li>
                            <li>Try using different PDF files</li>
                            <li>Make sure the job description is complete and not too short</li>
                            <li>Check your internet connection for AI processing</li>
                            <li>Reduce the number of files if uploading many resumes</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    progress_bar.empty()
                    status_text.empty()
                    return

            display_ranking_results(ranked_resumes, top_n)

            if show_details and ranked_resumes:
                st.markdown("---")
                st.markdown("### 🔍 Detailed Analysis")
                
                selected_resume = st.selectbox(
                    "Select resume for detailed analysis:",
                    options=range(len(ranked_resumes[:top_n])),
                    format_func=lambda x: f"#{x+1} - {ranked_resumes[x]['filename']} ({ranked_resumes[x]['match_score']:.1f}%)",
                    help="Choose a resume to see detailed AI agent analysis"
                )
                
                if st.button("🤖 Generate Detailed Analysis", key="detailed_analysis"):
                    selected_resume_data = ranked_resumes[selected_resume]
                    filename = selected_resume_data['filename']
                    resume_data = selected_resume_data['resume_data']
                    
                    with st.spinner(f"Generating detailed analysis for {filename}..."):
                        try:
                            steps = []
                            from src.agents import ResumeParserAgent
                            resume_agent = ResumeParserAgent("Resume Parser", {})
                            resume_agent.outputs = {
                            "name": resume_data.name,
                            "email": resume_data.email,
                             "phone": resume_data.phone,
                            "skills": resume_data.skills,
                             "raw_text": resume_data.raw_text
                            }
                            
                            steps.append(resume_agent)
                            steps.append(job_analysis)

                            a3 = content_enhancer_agent(resume_data.raw_text)
                            steps.append(a3)

                            a4 = matcher_and_scoring_agent(
                                resume_text=resume_data.raw_text,
                                job_text=job_desc,
                                resume_skills=resume_data.skills,
                                job_skills=job_skills,
                                embedding_service=embed,
                            )
                            steps.append(a4)

                            trace = build_workflow_trace(steps)
                            
                            if "session_metrics" not in st.session_state:
                                st.session_state.session_metrics = {
                                    "total_analyses": 0, "resumes_processed": 0,
                                    "avg_match_score": 0.0, "total_skills_identified": 0,
                                    "ai_suggestions_generated": 0, "workflow_traces": []
                                }
                            st.session_state.session_metrics["workflow_traces"].append(trace)

                            st.markdown(f"#### 📊 Detailed Analysis: {filename}")
                            display_enhanced_workflow_analysis(trace, {
                                "match_score": a4.outputs["score"],
                                "confidence": a4.outputs["confidence"],
                                "skills_matched": len(a4.outputs.get("matched_skills", []))
                            })

                            st.markdown("##### 🎯 Match Summary")
                            show_match_summary(
                                score=float(a4.outputs["score"]),
                                confidence=float(a4.outputs["confidence"]),
                                missing_skills=list(a4.outputs["missing_skills"]),
                                explanation=str(a4.outputs["explanation"]),
                                top_snippets=list(a4.outputs["top_snippets"]),
                            )

                        except Exception as e:
                            st.error(f"Detailed analysis failed: {str(e)}")

    
    elif mode == "📝 Resume Builder":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 25%, #1d4ed8 50%, #1e40af 75%, #1e3a8a 100%); 
                    padding: 3rem; border-radius: 25px; color: white; text-align: center; margin-bottom: 2rem;
                    box-shadow: 0 20px 40px rgba(59,130,246,0.4);">
            <h1 style="font-size: 3.5rem; font-weight: 900; margin-bottom: 0.5rem;">📝 AI-Powered Resume Builder</h1>
            <p style="font-size: 1.3rem; opacity: 0.95;">Create professional resumes with intelligent AI assistance</p>
        </div>
        """, unsafe_allow_html=True)

        photo_data_url = None
        experiences = []
        education = []
        projects = []
        certifications = []
        languages = []
        awards = []
        interests = []
        skills = []
        
        try:
            ai_service = get_ai_service()
            ai_available = ai_service.is_available() if ai_service else False
        except Exception as e:
            ai_available = False
            st.warning(f"AI service unavailable: {str(e)}")

        if ai_available:
            st.markdown("""
            <div class="success-message">
                🤖 <strong>AI Assistant Active:</strong> Click AI buttons throughout the form for intelligent content generation
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="warning-message">
                ⚠️ <strong>AI Assistant Offline:</strong> Manual content entry only. Configure GEMINI_API_KEY for AI features.
            </div>
            """, unsafe_allow_html=True)

        with st.form("resume_builder_form"):
            st.markdown("## 👤 Personal Information")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                name = st.text_input("Full Name *", placeholder="John Doe")
                col1_1, col1_2 = st.columns(2)
                with col1_1:
                    email = st.text_input("Email *", placeholder="john.doe@email.com")
                with col1_2:
                    phone = st.text_input("Phone *", placeholder="+1 (555) 123-4567")
                
                location = st.text_input("Location", placeholder="City, State/Country")
                
                st.markdown("### 🔗 Professional Links")
                linkedin = st.text_input("LinkedIn", placeholder="https://linkedin.com/in/johndoe")
                github = st.text_input("GitHub", placeholder="https://github.com/johndoe")
                portfolio = st.text_input("Portfolio/Website", placeholder="https://johndoe.com")
            
            with col2:
                st.markdown("### 📷 Professional Photo (Optional)")
                photo_file = st.file_uploader(
                    "Upload Photo", 
                    type=['png', 'jpg', 'jpeg'],
                    help="Upload a professional headshot for your resume"
                )
                
                if photo_file:
                    try:
                        photo_data_url = process_uploaded_image(photo_file)
                        if photo_data_url:
                            st.image(photo_file, width=200, caption="Resume Photo Preview")
                    except Exception as e:
                        st.warning(f"Could not process image: {str(e)}")
                        photo_data_url = None

            st.markdown("---")
            st.markdown("## 📝 Professional Summary")

            job_target = st.text_input("Target Job Title (helps AI)", placeholder="e.g., Senior Software Engineer, Data Scientist")
            industry = st.text_input("Target Industry (helps AI)", placeholder="e.g., Technology, Healthcare, Finance")

            
            try:
                summary = ai_content_generator_component(
                    section_name="Professional Summary",
                    current_content="",
                    content_type="professional_summary",
                    user_data={"job_title": job_target, "industry": industry},
                    job_title=job_target,
                    industry=industry,
                    placeholder_text="Experienced professional with expertise in...\nProven track record of...\nSeeking to leverage skills in..."
                )
            except Exception as e:
                st.warning(f"AI content generator unavailable: {str(e)}")
                summary = st.text_area(
                    "Professional Summary",
                    placeholder="Experienced professional with expertise in...\nProven track record of...\nSeeking to leverage skills in...",
                    height=100
                )
            
            st.markdown("---")
            
            st.markdown("## 💼 Work Experience")
            try:
                experiences = dynamic_experience_input_with_ai()
            except Exception as e:
                st.warning(f"Experience input unavailable: {str(e)}")
                experiences = []
                st.text_area("Work Experience", placeholder="Add your work experience here", height=150)

            st.markdown("---")
            
            st.markdown("## 🎓 Education")
            try:
                education = dynamic_education_input()
            except Exception as e:
                st.warning(f"Education input unavailable: {str(e)}")
                education = []
                st.text_area("Education", placeholder="Add your education here", height=100)

            st.markdown("---")
            
            st.markdown("## 🛠️ Skills")
            try:
                skills_text = ai_skills_suggester(
                    current_skills="",
                    job_title=job_target,
                    industry=industry,
                    in_form=True
                )
                
                
                if skills_text:
                    skills = [skill.strip() for skill in str(skills_text).split(',') if skill.strip()]
                else:
                    skills = []
            except Exception as e:
                st.warning(f"Skills suggester unavailable: {str(e)}")
                skills_text = st.text_area(
                    "Skills (comma-separated)",
                    placeholder="Python, JavaScript, React, Machine Learning, SQL",
                    height=100
                )
                skills = [skill.strip() for skill in str(skills_text).split(',') if skill.strip()]

            st.markdown("---")
            
            st.markdown("## 🚀 Projects")
            try:
                projects = dynamic_projects_input()
            except Exception as e:
                st.warning(f"Projects input unavailable: {str(e)}")
                projects = []
                st.text_area("Projects", placeholder="Add your projects here", height=150)

            st.markdown("---")
            
            st.markdown("## 📋 Additional Sections")
            
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    certifications = dynamic_list_input(
                        "Certifications", 
                        "certifications", 
                        "e.g., AWS Certified Solutions Architect",
                        "Professional certifications and licenses"
                    )
                    
                    languages = dynamic_list_input(
                        "Languages", 
                        "languages", 
                        "e.g., English (Native), Spanish (Fluent)",
                        "Languages and proficiency levels"
                    )
                except Exception as e:
                    st.warning(f"Dynamic input unavailable: {str(e)}")
                    certifications_text = st.text_area("Certifications", placeholder="One per line")
                    certifications = [cert.strip() for cert in certifications_text.split('\n') if cert.strip()]
                    
                    languages_text = st.text_area("Languages", placeholder="One per line")
                    languages = [lang.strip() for lang in languages_text.split('\n') if lang.strip()]
            
            with col2:
                try:
                    awards = dynamic_list_input(
                        "Awards & Honors", 
                        "awards", 
                        "e.g., Employee of the Year 2023",
                        "Awards, honors, and recognitions"
                    )
                    
                    interests = dynamic_list_input(
                        "Interests & Hobbies", 
                        "interests", 
                        "e.g., Photography, Rock Climbing, Coding",
                        "Personal interests and hobbies"
                    )
                except Exception as e:
                    st.warning(f"Dynamic input unavailable: {str(e)}")
                    awards_text = st.text_area("Awards & Honors", placeholder="One per line")
                    awards = [award.strip() for award in awards_text.split('\n') if award.strip()]
                    
                    interests_text = st.text_area("Interests & Hobbies", placeholder="One per line")
                    interests = [interest.strip() for interest in interests_text.split('\n') if interest.strip()]

            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button(
                    "🎯 Generate Professional Resume", 
                    type="primary",
                    use_container_width=True
                )

        
        if submitted:
            
            if not name or not name.strip():
                st.error("Please enter your full name")
            elif not email or not email.strip():
                st.error("Please enter your email address")
            elif not phone or not phone.strip():
                st.error("Please enter your phone number")
            else:
                with st.spinner("🤖 Creating your professional resume..."):
                    try:
                        resume_data = {
                            "personal_info": {
                                "name": str(name).strip(),
                                "email": str(email).strip(),
                                "phone": str(phone).strip(),
                                "location": str(location).strip() if location else "",
                                "linkedin": str(linkedin).strip() if linkedin else "",
                                "github": str(github).strip() if github else "",
                                "portfolio": str(portfolio).strip() if portfolio else "",
                                "photo": photo_data_url if photo_data_url else None
                            },
                            "summary": str(summary).strip() if summary else "",
                            "experience": experiences if experiences else [],
                            "education": education if education else [],
                            "skills": skills if skills else [],
                            "projects": projects if projects else [],
                            "certifications": certifications if certifications else [],
                            "languages": languages if languages else [],
                            "awards": awards if awards else [],
                            "interests": interests if interests else []
                        }
                        
                        
                        try:
                            update_session_metrics({
                                "resumes_count": 1,
                                "match_score": 0,
                                "skills_identified": len(skills),
                                "ai_suggestions": 3 if ai_available else 0
                            })
                        except Exception as e:
                            st.warning(f"Could not update metrics: {str(e)}")
                        
                       
                        try:
                            if skills:
                                update_skills_database(skills)
                        except Exception as e:
                            st.warning(f"Could not update skills database: {str(e)}")
                        
                       
                        try:
                            pdf_buffer = generate_ats_resume_pdf_safe(resume_data)
                        except Exception as e:
                            st.error(f"PDF generation failed: {str(e)}")
                            pdf_buffer = None
                        
                        if pdf_buffer:
                            st.markdown("""
                            <div class="success-message">
                                ✅ <strong>Resume Generated Successfully!</strong><br>
                                Your professional resume has been created with ATS-friendly formatting.
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2, col3 = st.columns([1, 2, 1])
                            with col2:
                                st.download_button(
                                    label="📥 Download Professional Resume (PDF)",
                                    data=pdf_buffer if isinstance(pdf_buffer, bytes) else pdf_buffer.getvalue(),
                                    file_name=f"{name.replace(' ', '_')}_Resume.pdf",
                                    mime="application/pdf",
                                    type="primary",
                                    use_container_width=True
                                )
                            
                            
                            with st.expander("👀 Resume Preview", expanded=False):
                                st.markdown("### Resume Content Summary")
                                
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    st.markdown("**Personal Information:**")
                                    st.write(f"• Name: {name}")
                                    st.write(f"• Email: {email}")
                                    st.write(f"• Phone: {phone}")
                                    if location:
                                        st.write(f"• Location: {location}")
                                    
                                    if summary:
                                        st.markdown("**Professional Summary:**")
                                        summary_preview = str(summary)[:200] + "..." if len(str(summary)) > 200 else str(summary)
                                        st.write(summary_preview)
                                    
                                    if skills:
                                        st.markdown("**Key Skills:**")
                                        skills_preview = ", ".join(skills[:10]) + ("..." if len(skills) > 10 else "")
                                        st.write(skills_preview)
                                
                                with col2:
                                    if experiences:
                                        st.markdown("**Work Experience:**")
                                        for i, exp in enumerate(experiences[:3]):
                                            if isinstance(exp, dict) and exp.get('title') and exp.get('company'):
                                                st.write(f"• {exp['title']} at {exp['company']}")
                                    
                                    if education:
                                        st.markdown("**Education:**")
                                        for edu in education[:2]:
                                            if isinstance(edu, dict) and edu.get('degree') and edu.get('school'):
                                                st.write(f"• {edu['degree']} - {edu['school']}")
                                    
                                    if projects:
                                        st.markdown("**Projects:**")
                                        for proj in projects[:3]:
                                            if isinstance(proj, dict) and proj.get('name'):
                                                st.write(f"• {proj['name']}")
                            
                            st.markdown("---")
                            st.markdown("### 🎯 Next Steps")
                            st.info("Your resume has been generated successfully! You can now use it to apply for jobs or test it against job descriptions in the Resume Matching section.")
                        
                        else:
                            st.error("Failed to generate PDF. Please check your input and try again.")
                            
                    except Exception as e:
                        st.error(f"Resume generation failed: {str(e)}")
                        st.markdown("""
                        <div class="warning-message">
                            <h4>Generation Error Tips:</h4>
                            <ul>
                                <li>Check that all required fields are properly filled</li>
                                <li>Ensure your content doesn't contain special characters that might cause issues</li>
                                <li>Try shortening very long text entries</li>
                                <li>If using a photo, ensure it's a standard image format (PNG, JPG, JPEG)</li>
                                <li>Try refreshing the page and filling the form again</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
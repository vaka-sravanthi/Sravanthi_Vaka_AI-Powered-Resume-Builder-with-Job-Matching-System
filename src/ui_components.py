from __future__ import annotations

from typing import List, Tuple, Dict, Any, Optional
import plotly.graph_objects as go
import streamlit as st
from src.ai_content_generator import get_ai_service


def show_workflow_diagram(fig: go.Figure) -> None:
    st.subheader("Workflow Visualization")
    st.plotly_chart(fig, use_container_width=True)


def show_agent_outputs(outputs: List[Tuple[str, dict]]) -> None:
    with st.expander("Agent Outputs", expanded=False):
        for name, data in outputs:
            st.markdown(f"**{name}**")
            st.json(data)


def show_match_summary(score: float, confidence: float, missing_skills: List[str], explanation: str, top_snippets: List[Tuple[str, float]]) -> None:
    st.subheader("Results")
    cols = st.columns(3)
    cols[0].metric("Match Score", f"{score:.1f}%")
    cols[1].metric("Confidence", f"{confidence:.2f}")
    cols[2].metric("Top Snippets", f"{len(top_snippets)}")

    if missing_skills:
        st.markdown("**Skill Gaps**: " + ", ".join(missing_skills))
    st.markdown("**Explanation**")
    st.write(explanation)

    if top_snippets:
        st.markdown("**Top Matching Snippets**")
        for text, sim in top_snippets[:5]:
            st.write(f"{sim:.2f} — {text}")


def ai_content_generator_component(
    section_name: str,
    current_content: str = "",
    content_type: str = "general",
    user_data: Dict[str, Any] = None,
    job_title: str = "",
    industry: str = "",
    placeholder_text: str = "",
    height: int = 150,
    in_form: bool = True,
    experience_index: int = 0
) -> str:
    if user_data is None:
        user_data = {}
    
    text_key = f"{section_name.lower().replace(' ', '_').replace('-', '_')}_text_{experience_index}"
    ai_key = f"{section_name.lower().replace(' ', '_').replace('-', '_')}_ai_{experience_index}"
    
    if text_key not in st.session_state:
        st.session_state[text_key] = current_content
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        content = st.text_area(
            section_name,
            value=st.session_state.get(text_key, current_content),
            key=f"{text_key}_input",
            placeholder=placeholder_text,
            height=height,
            help=f"Enter your {section_name.lower()} or use AI to generate content"
        )
        st.session_state[text_key] = content
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        ai_service = get_ai_service()
        
        if ai_service.is_available():
            if in_form:
                if content_type == "professional_summary":
                    button_text = f"🤖 Summary"
                elif content_type == "work_experience":
                    button_text = f"🤖 Work {experience_index}"
                elif content_type == "projects":
                    button_text = f"🚀 Project {experience_index}"
                else:
                    button_text = f"🤖 AI {experience_index}"
                ai_clicked = st.form_submit_button(button_text, help=f"Generate {section_name.lower()} using AI")
            else:
                ai_clicked = st.button(f"🤖 AI", key=ai_key, help=f"Generate {section_name.lower()} using AI", type="secondary")
                
            if ai_clicked:
                with st.spinner(f"🤖 Generating {section_name.lower()}..."):
                    try:
                        context = {
                            "content_type": content_type,
                            "job_title": job_title,
                            "industry": industry,
                            "current_content": content,
                            **user_data
                        }
                        
                        if content_type == "professional_summary":
                            prompt = f"""Create a professional summary for a {job_title or 'professional'} in the {industry or 'technology'} industry. 
                            Make it compelling, specific, and ATS-friendly. Focus on achievements and value proposition.
                            
                            Current content: {content or 'None'}
                            
                            Generate a 3-4 sentence professional summary that highlights key skills and experience."""
                            
                        elif content_type == "work_experience":
                            prompt = f"""Create compelling bullet points for work experience as a {job_title or user_data.get('job_title', 'professional')} 
                            at {user_data.get('company', 'a company')}. 
                            
                            Make the bullet points:
                            - Start with strong action verbs
                            - Include quantifiable achievements when possible
                            - Be specific and results-oriented
                            - ATS-friendly
                            
                            Current content: {content or 'None'}
                            
                            Generate 3-5 bullet points describing key responsibilities and achievements."""
                            
                        elif content_type == "projects":
                            project_name = user_data.get('project_name', 'the project')
                            technologies = user_data.get('technologies', '')
                            
                            prompt = f"""Create a compelling project description for "{project_name}" on a resume.
                            
                            Project details:
                            - Technologies used: {technologies or 'Various technologies'}
                            - Target role: {job_title or 'Software Developer'}
                            - Industry: {industry or 'Technology'}
                            
                            Current content: {content or 'None'}
                            
                            Create a professional project description that includes:
                            - Brief overview of what the project does
                            - Key technologies and tools used
                            - Your specific role and contributions
                            - Quantifiable impact or results (if applicable)
                            - Technical challenges solved
                            
                            Format as 2-4 bullet points starting with strong action verbs.
                            Make it relevant for the target role and showcase technical skills."""
                            
                        else:
                            prompt = f"""Create professional content for {section_name} section of a resume.
                            Target role: {job_title or 'Professional'}
                            Industry: {industry or 'General'}
                            
                            Current content: {content or 'None'}
                            
                            Generate relevant, professional content that would be appropriate for this section."""
                        
                        generated_content = ai_service.generate_content(prompt)
                        
                        if generated_content:
                            st.session_state[text_key] = generated_content
                            st.success("✅ Content generated!")
                            if not in_form:
                                st.rerun()
                        else:
                            st.warning("AI generation returned empty content. Try again.")
                            
                    except Exception as e:
                        st.error(f"AI generation failed: {str(e)}")
        else:
            st.warning("🤖 AI Offline")
    
    return st.session_state.get(text_key, current_content)


def ai_skills_suggester(
    current_skills: str = "",
    job_title: str = "",
    industry: str = "",
    in_form: bool = True,
    skills_index: int = 0
) -> str:
    skills_key = f"skills_text_{skills_index}"
    ai_skills_key = f"skills_ai_{skills_index}"
    
    if skills_key not in st.session_state:
        st.session_state[skills_key] = current_skills
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        skills_input = st.text_area(
            "Skills (comma-separated)",
            value=st.session_state.get(skills_key, current_skills),
            key=f"{skills_key}_input",
            placeholder="Python, JavaScript, React, Machine Learning, Project Management, Communication",
            height=100,
            help="List your skills separated by commas, or use AI to generate relevant skills"
        )
        st.session_state[skills_key] = skills_input
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        ai_service = get_ai_service()
        
        if ai_service.is_available():
            if in_form:
                button_text = f"🎯 AI {skills_index}"
                ai_clicked = st.form_submit_button(button_text, help="Get AI-suggested skills for your target role")
            else:
                ai_clicked = st.button("🎯 AI", key=ai_skills_key, help="Get AI-suggested skills for your target role", type="secondary")
                
            if ai_clicked:
                with st.spinner("🧠 Analyzing skill requirements..."):
                    try:
                        prompt = f"""Suggest relevant skills for a {job_title or 'professional'} in the {industry or 'technology'} industry.
                        
                        Current skills: {skills_input or 'None provided'}
                        
                        Provide a comprehensive list of skills including:
                        - Technical skills relevant to the role
                        - Soft skills important for the position
                        - Industry-specific competencies
                        - Tools and technologies commonly used
                        
                        Format as a comma-separated list. Include 15-20 relevant skills.
                        Mix of technical and soft skills. Be specific and current with technology trends."""
                        
                        generated_skills = ai_service.generate_content(prompt)
                        
                        if generated_skills:
                            existing_skills = [s.strip() for s in skills_input.split(',') if s.strip()]
                            suggested_skills_list = [s.strip() for s in generated_skills.split(',') if s.strip()]
                            
                            all_skills = list(dict.fromkeys(existing_skills + suggested_skills_list))
                            combined_skills = ', '.join(all_skills)
                            
                            st.session_state[skills_key] = combined_skills
                            st.success("✅ Skills enhanced with AI suggestions!")
                            if not in_form:
                                st.rerun()
                        else:
                            st.warning("AI skills generation returned empty content. Try again.")
                            
                    except Exception as e:
                        st.error(f"AI skills generation failed: {str(e)}")
        else:
            st.warning("🤖 AI Offline")
    
    return st.session_state.get(skills_key, current_skills)


def professional_summary_with_ai(user_data: Dict[str, Any], job_title: str = "", industry: str = "", index: int = 0) -> str:
    st.markdown("### Professional Summary")
    
    return ai_content_generator_component(
        section_name="Professional Summary",
        current_content="",
        content_type="professional_summary",
        user_data=user_data,
        job_title=job_title,
        industry=industry,
        placeholder_text="A brief professional summary highlighting your key strengths and experience...",
        height=120,
        in_form=True,
        experience_index=index
    )


def work_experience_with_ai(job_title: str, company: str, user_data: Dict[str, Any] = None, experience_index: int = 0) -> str:
    if user_data is None:
        user_data = {}
    
    user_data.update({"job_title": job_title, "company": company})
    
    return ai_content_generator_component(
        section_name=f"Work Experience {experience_index} - {job_title}",
        current_content="",
        content_type="work_experience",
        user_data=user_data,
        job_title=job_title,
        industry="",
        placeholder_text="• Led cross-functional teams...\n• Increased efficiency by 25%...\n• Managed budget of $X...",
        height=150,
        in_form=True,
        experience_index=experience_index
    )


def work_experience_section_with_ai(job_title: str, company: str, user_data: Dict[str, Any] = None, experience_index: int = 0) -> str:
    if user_data is None:
        user_data = {}
    
    st.markdown(f"### 🏢 Experience {experience_index + 1}")
    st.markdown(f"**{job_title}** at **{company}**")
    
    user_data.update({"job_title": job_title, "company": company})
    
    return ai_content_generator_component(
        section_name=f"Work Description",
        current_content="",
        content_type="work_experience",
        user_data=user_data,
        job_title=job_title,
        industry="",
        placeholder_text="• Led cross-functional teams to deliver projects ahead of schedule\n• Increased system efficiency by 25% through optimization\n• Managed budget of $50K+ for department initiatives",
        height=150,
        in_form=True,
        experience_index=experience_index
    )


def project_description_component(project_name: str, technologies: str = "", user_data: Dict[str, Any] = None, project_index: int = 0) -> str:
    if user_data is None:
        user_data = {}
    
    text_key = f"project_description_text_{project_index}"
    
    if text_key not in st.session_state:
        st.session_state[text_key] = ""
    
    content = st.text_area(
        "Project Description",
        value=st.session_state.get(text_key, ""),
        key=f"{text_key}_input",
        placeholder="• Developed a full-stack web application using React and Node.js\n• Implemented RESTful APIs with 99.9% uptime\n• Reduced load time by 40% through optimization",
        height=150,
        help="Enter your project description and key achievements"
    )
    
    st.session_state[text_key] = content
    
    return st.session_state.get(text_key, "")


def project_section_component(project_name: str, technologies: str = "", user_data: Dict[str, Any] = None, project_index: int = 0) -> str:
    if user_data is None:
        user_data = {}
    
    st.markdown(f"### 🚀 Project {project_index + 1}")
    st.markdown(f"**{project_name}**")
    if technologies:
        st.markdown(f"*Technologies: {technologies}*")
    
    text_key = f"project_section_text_{project_index}"
    
    if text_key not in st.session_state:
        st.session_state[text_key] = ""
    
    content = st.text_area(
        "Project Description",
        value=st.session_state.get(text_key, ""),
        key=f"{text_key}_input",
        placeholder="• Developed a full-stack web application using React and Node.js\n• Implemented RESTful APIs with 99.9% uptime\n• Reduced load time by 40% through code optimization\n• Integrated third-party services for enhanced functionality",
        height=150,
        help="Enter your project description and key achievements"
    )
    
    st.session_state[text_key] = content
    
    return st.session_state.get(text_key, "")
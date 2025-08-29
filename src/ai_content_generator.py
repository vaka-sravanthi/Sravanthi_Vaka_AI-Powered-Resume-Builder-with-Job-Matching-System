import os
import google.generativeai as genai
from typing import Dict, Any, Optional, List
import streamlit as st

class AIContentGenerator:
    
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
    
    def is_available(self) -> bool:
        
        return self.model is not None
    
    def generate_content(self, prompt: str) -> str:
        
        if not self.is_available():
            return "AI service not available. Please add your GEMINI_API_KEY to use AI features."
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Error generating content: {str(e)}"
    
    def _format_education(self, education: List[Dict]) -> str:
       
        if not education:
            return "Not specified"
        
        formatted = []
        for edu in education:
            degree = edu.get('degree', '')
            institution = edu.get('institution', '')
            year = edu.get('year', '')
            formatted.append(f"{degree} from {institution} ({year})")
        return '; '.join(formatted)
    
    def _format_experience(self, experience: List[Dict]) -> str:
       
        if not experience:
            return "Not specified"
        
        formatted = []
        for exp in experience:
            company = exp.get('company', '')
            position = exp.get('position', '')
            duration = exp.get('duration', '')
            formatted.append(f"{position} at {company} ({duration})")
        return '; '.join(formatted)
    
    def generate_professional_summary(self, user_data: Dict[str, Any], 
                                    job_title: str = "", 
                                    industry: str = "",
                                    custom_prompt: str = "") -> str:
        
        if not self.is_available():
            return "AI service not available. Please add your GEMINI_API_KEY to use AI features."
        
        try:
            experience_years = user_data.get('experience_years', 0)
            skills = user_data.get('skills', [])
            education = user_data.get('education', [])
            experience = user_data.get('experience', [])
            
            base_prompt = f"""
            Create a professional and compelling resume summary (2-4 sentences) based on the following information:
            
            Target Job Title: {job_title or 'Professional'}
            Industry: {industry or 'General'}
            Years of Experience: {experience_years}
            
            Key Skills: {', '.join(skills) if skills else 'Not specified'}
            
            Education: {self._format_education(education)}
            
            Work Experience: {self._format_experience(experience)}
            
            {f"Additional Requirements: {custom_prompt}" if custom_prompt else ""}
            
            Guidelines:
            - Write in third person or first person (professional tone)
            - Highlight key strengths and achievements
            - Keep it concise and impactful
            - Focus on value proposition
            - Make it ATS-friendly
            
            Generate only the professional summary text, no additional formatting or labels:
            """
            
            response = self.model.generate_content(base_prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Error generating content: {str(e)}"
    
    def generate_work_experience_description(self, 
                                           job_title: str,
                                           company: str,
                                           responsibilities: str = "",
                                           achievements: str = "",
                                           custom_prompt: str = "") -> str:
        """Generate work experience description"""
        if not self.is_available():
            return "AI service not available."
        
        try:
            prompt = f"""
            Create professional bullet points for a work experience entry:
            
            Job Title: {job_title}
            Company: {company}
            Key Responsibilities: {responsibilities}
            Achievements: {achievements}
            
            {f"Additional Context: {custom_prompt}" if custom_prompt else ""}
            
            Guidelines:
            - Create 3-5 bullet points
            - Start each bullet with strong action verbs
            - Include quantifiable results where possible
            - Focus on achievements and impact
            - Use professional language
            - Make it ATS-friendly
            
            Generate only the bullet points, one per line with • symbol:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Error generating content: {str(e)}"
    
    def generate_project_description(self,
                                   project_name: str,
                                   technologies: str = "",
                                   project_type: str = "",
                                   target_job_title: str = "",
                                   industry: str = "",
                                   current_description: str = "",
                                   custom_prompt: str = "") -> str:
        """Generate project description for resume"""
        if not self.is_available():
            return "AI service not available."
        
        try:
            prompt = f"""
            Create a compelling project description for a resume:
            
            Project Name: {project_name}
            Technologies Used: {technologies or 'Various technologies'}
            Project Type: {project_type or 'Software project'}
            Target Job Role: {target_job_title or 'Software Developer'}
            Industry: {industry or 'Technology'}
            Current Description: {current_description or 'None provided'}
            
            {f"Additional Context: {custom_prompt}" if custom_prompt else ""}
            
            Guidelines:
            - Create 3-4 professional bullet points
            - Start with strong action verbs (Developed, Implemented, Built, Created, etc.)
            - Highlight key technologies and tools used
            - Include quantifiable results where possible (performance improvements, user metrics, etc.)
            - Show your specific role and contributions
            - Mention technical challenges solved
            - Make it relevant for the target job role
            - Use professional, ATS-friendly language
            - Focus on impact and technical skills demonstrated
            
            Examples of good project bullets:
            • Developed a full-stack e-commerce platform using React.js and Node.js, serving 1000+ daily active users
            • Implemented RESTful APIs with JWT authentication, achieving 99.5% uptime and sub-200ms response times
            • Built responsive UI components with modern CSS frameworks, improving user engagement by 35%
            • Integrated third-party payment gateways and real-time notifications using WebSocket technology
            
            Generate only the bullet points, one per line with • symbol:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Error generating content: {str(e)}"
    
    def suggest_project_technologies(self,
                                   project_name: str,
                                   project_type: str = "",
                                   target_job_title: str = "",
                                   industry: str = "") -> List[str]:
        """Suggest relevant technologies for a project based on job requirements"""
        if not self.is_available():
            return []
        
        try:
            prompt = f"""
            Suggest 8-12 relevant technologies and tools for a project:
            
            Project Name: {project_name}
            Project Type: {project_type or 'Software project'}
            Target Job Role: {target_job_title or 'Software Developer'}
            Industry: {industry or 'Technology'}
            
            Guidelines:
            - Include programming languages, frameworks, databases, and tools
            - Focus on technologies relevant to the target job role
            - Mix of frontend, backend, and other relevant technologies
            - Include both specific technologies and general categories
            - Make suggestions realistic and commonly used together
            - Consider current industry trends and demands
            
            Examples:
            For a web application: React.js, Node.js, MongoDB, Express.js, HTML5, CSS3, JavaScript, Git
            For a mobile app: React Native, Firebase, REST APIs, Redux, AsyncStorage
            For data analysis: Python, Pandas, NumPy, Matplotlib, Jupyter Notebook, SQL
            
            Provide only technology names, one per line, no bullets or numbering:
            """
            
            response = self.model.generate_content(prompt)
            technologies_text = response.text.strip()

            technologies = [tech.strip() for tech in technologies_text.split('\n') if tech.strip()]
            return technologies
            
        except Exception as e:
            return []
    
    def generate_skills_suggestions(self, 
                                  job_title: str = "",
                                  industry: str = "",
                                  current_skills: List[str] = [],
                                  custom_prompt: str = "") -> List[str]:
        """Generate relevant skills suggestions"""
        if not self.is_available():
            return []
        
        try:
            prompt = f"""
            Suggest 10-15 relevant professional skills for:
            
            Job Title: {job_title}
            Industry: {industry}
            Current Skills: {', '.join(current_skills) if current_skills else 'None listed'}
            
            {f"Additional Requirements: {custom_prompt}" if custom_prompt else ""}
            
            Guidelines:
            - Mix of technical and soft skills
            - Industry-relevant
            - Modern and in-demand skills
            - Avoid duplicating current skills
            - Include both specific tools and general competencies
            
            Provide only skill names, one per line, no bullets or numbering:
            """
            
            response = self.model.generate_content(prompt)
            skills_text = response.text.strip()
            skills = [skill.strip() for skill in skills_text.split('\n') if skill.strip()]
            return skills
            
        except Exception as e:
            return []
    
    def improve_existing_content(self, 
                               current_content: str,
                               content_type: str = "general",
                               custom_prompt: str = "") -> str:
        """Improve existing resume content"""
        if not self.is_available():
            return current_content
        
        try:
            prompt = f"""
            Improve the following resume {content_type} content:
            
            Current Content:
            {current_content}
            
            {f"Specific Instructions: {custom_prompt}" if custom_prompt else ""}
            
            Guidelines:
            - Make it more professional and impactful
            - Improve clarity and readability
            - Use stronger action verbs
            - Make it more ATS-friendly
            - Keep the same general meaning but enhance presentation
            - Maintain appropriate length
            
            Provide only the improved content:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return current_content

@st.cache_resource
def get_ai_service():
    """Get cached AI service instance"""
    return AIContentGenerator()
"""
AI Service for ENSA HR Module
Handles OpenAI GPT-4 integration for intelligent insights and analysis
"""
import logging
import json
from typing import List, Dict, Any, Optional
import requests
from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AIService:
    """Base AI Service using OpenAI GPT-4"""
    
    def __init__(self, provider: str = "openai", openai_key: str = None, gemini_key: str = None, huggingface_key: str = None, model: str = None):
        """
        Initialize AI Service with provider selection
        """
        self.provider = provider
        self.openai_key = openai_key
        self.gemini_key = gemini_key
        self.huggingface_key = huggingface_key
        
        # Default models per provider if not specified
        if not model:
            if provider == "openai":
                self.model = "gpt-4o-mini"
            elif provider == "gemini":
                self.model = "gemini-flash-latest"
            elif provider == "huggingface":
                self.model = "google/gemma-2-2b-it"
        else:
            self.model = model
            
        self._cache = {}

    # ... generate_text method update in next chunk ...

# ...


    
    def generate_text(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Generate text using the configured provider"""
        try:
            # Check cache first
            cache_key = f"{self.provider}_{prompt[:100]}_{max_tokens}_{temperature}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            _logger.info(f"Generating AI text with provider {self.provider} / model {self.model}")
            
            result = ""
            if self.provider == 'openai':
                result = self._generate_openai(prompt, max_tokens, temperature)
            elif self.provider == 'gemini':
                result = self._generate_gemini(prompt, max_tokens, temperature)
            elif self.provider == 'huggingface':
                result = self._generate_huggingface(prompt, max_tokens, temperature)
            else:
                raise UserError(_("Unknown AI provider: %s") % self.provider)
            
            # Cache the result
            self._cache[cache_key] = result.strip()
            return result.strip()
            
        except Exception as e:
            _logger.error(f"AI generation error: {str(e)}")
            raise UserError(_("AI service error: %s") % str(e))

    # ... _generate_openai ...

    # ... _generate_gemini ...

    def _generate_huggingface(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call Hugging Face Inference API via Router (OpenAI Compatible)"""
        if not self.huggingface_key:
             raise UserError(_("Hugging Face access token is missing"))
        
        # Use Router URL with OpenAI Compatibility
        # This replaces the deprecated api-inference.huggingface.co
        api_url = "https://router.huggingface.co/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.huggingface_key}",
            "Content-Type": "application/json"
        }
        
        # Construct payload using OpenAI Chat Completion + parameters
        # The router handles the chat template application automatically
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": max(0.1, temperature),
            "stream": False
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            # Parse OpenAI-style response
            try:
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    return str(result)
            except (KeyError, IndexError) as e:
                _logger.error(f"Failed to parse Hugging Face response: {result}")
                raise UserError(f"Hugging Face Response Parsing Error: {str(e)}")
        else:
             # Handle 503 Model Loading
             if response.status_code == 503:
                 raise UserError("Model is loading (cold boot). Please try again in 30 seconds.")
             
             # Try to extract error message definition
             error_msg = response.text
             try:
                 error_json = response.json()
                 if 'error' in error_json:
                     error_msg = error_json['error']
             except:
                 pass
                 
             raise UserError(f"Hugging Face Error: {error_msg}")

    def _generate_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call OpenAI Chat Completions API"""
        if not self.openai_key:
             raise UserError(_("OpenAI API key is missing"))

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert HR analyst providing insights."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise UserError(f"OpenAI Error: {response.text}")

    def _generate_gemini(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call Google Gemini REST API"""
        if not self.gemini_key:
             raise UserError(_("Gemini API key is missing"))
        
        # Model Mapping: UI Selection -> Actual API ID
        # The API requires specific version IDs or valid aliases from ListModels
        model_map = {
            # Direct valid aliases
            'gemini-flash-latest': 'gemini-flash-latest',
            'gemini-pro-latest': 'gemini-pro-latest',
            # Mappings for legacy/invalid keys -> New Valid Models
            'gemini-1.5-flash': 'gemini-flash-latest',
            'gemini-1.5-flash-latest': 'gemini-flash-latest',
            'gemini-1.5-pro-latest': 'gemini-pro-latest',
            'gemini-pro': 'gemini-pro-latest',
        }
        
        # Use mapped ID or fallback to the raw model string
        api_model = model_map.get(self.model, self.model)
             
        # Gemini API Endpoint (v1beta)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{api_model}:generateContent?key={self.gemini_key}"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            try:
                # Extract text from Gemini response structure
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
            except (KeyError, IndexError):
                _logger.error(f"Unexpected Gemini response structure: {data}")
                return "Error: Could not parse Gemini response."
        else:
             raise UserError(f"Gemini Error: {response.text}")

    
    def analyze_performance(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze employee performance using AI
        
        Args:
            employee_data: Dictionary with employee performance metrics
            
        Returns:
            Analysis results with insights and recommendations
        """
        prompt = f"""
Analyze this employee's performance data and provide insights:

Employee: {employee_data.get('name', 'Unknown')}
Department: {employee_data.get('department', 'Unknown')}
Recent Evaluation Scores: {employee_data.get('scores', [])}
Average Score: {employee_data.get('avg_score', 0):.1f}/10
Trend: {employee_data.get('trend', 'Unknown')}
Training Completed: {employee_data.get('training_count', 0)}
Tenure: {employee_data.get('tenure', 0)} years

Provide:
1. Brief performance summary (2-3 sentences)
2. Key strengths
3. Areas for improvement
4. Recommendation (promote/retain/improve/develop)
5. Suggested next steps

Format as JSON with keys: summary, strengths, improvements, recommendation, next_steps
"""
        
        response_text = self.generate_text(prompt, max_tokens=600, temperature=0.5)
        
        try:
            # Try to parse JSON response
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback if not valid JSON
            result = {
                "summary": response_text,
                "recommendation": "retain"
            }
        
        return result
    
    def detect_turnover_risk(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict employee turnover risk using AI analysis
        
        Args:
            employee_data: Employee performance and engagement data
            
        Returns:
            Risk assessment with score and factors
        """
        prompt = f"""
Assess turnover risk for this employee:

Performance Trend: {employee_data.get('trend', 'stable')}
Recent Scores: {employee_data.get('recent_scores', [])}
Average Score: {employee_data.get('avg_score', 0):.1f}/10
Last Evaluation: {employee_data.get('days_since_eval', 0)} days ago
Training Participation: {employee_data.get('training_count', 0)} courses
Tenure: {employee_data.get('tenure', 0)} years
Has Certifications: {employee_data.get('has_certs', False)}

Assess turnover risk (0-100%) and identify top 3 risk factors.
Format as JSON: {{"risk_score": 0-100, "risk_level": "low/medium/high", "factors": ["factor1", "factor2", "factor3"], "mitigation": "action to take"}}
"""
        
        response_text = self.generate_text(prompt, max_tokens=400, temperature=0.3)
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Default low risk if parsing fails
            result = {
                "risk_score": 30,
                "risk_level": "low",
                "factors": ["Insufficient data"],
                "mitigation": "Continue monitoring"
            }
        
        return result
    
    def answer_query(self, question: str, context_data: Dict[str, Any]) -> str:
        """
        Answer natural language questions about HR data
        
        Args:
            question: User's question
            context_data: Relevant HR data for context
            
        Returns:
            Natural language answer
        """
        prompt = f"""
Answer this HR question based on the data:

Question: {question}

Available Data:
- Total Employees: {context_data.get('total_employees', 0)}
- Average Performance Score: {context_data.get('avg_performance', 0):.1f}/10
- Departments: {context_data.get('departments', [])}
- Recent Evaluations: {context_data.get('recent_evaluations', 0)}
- Training Programs: {context_data.get('training_programs', 0)}
- Active Internships: {context_data.get('active_internships', 0)}
- Active Projects: {context_data.get('active_projects', 0)}

Additional Context: {json.dumps(context_data.get('extra', {}), indent=2)}

Provide a clear, data-driven answer in 2-4 sentences. Include specific numbers.
"""
        
        return self.generate_text(prompt, max_tokens=300, temperature=0.6)
    
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for text via direct HTTP request
        """
        if self.provider != 'openai':
            # TODO: Implement Gemini embeddings (models/embedding-001)
            _logger.warning("Embeddings not yet supported for provider: %s", self.provider)
            return []

        try:
            url = "https://api.openai.com/v1/embeddings"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_key}"
            }
            payload = {
                "input": text,
                "model": "text-embedding-ada-002"
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                return response.json()['data'][0]['embedding']
            else:
                _logger.error(f"Embedding error: {response.text}")
                return []
        except Exception as e:
            _logger.error(f"Embedding generation error: {str(e)}")
            return []
    
    def detect_anomalies(self, data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in HR metrics using AI
        
        Args:
            data_points: List of data points to analyze
            
        Returns:
            List of detected anomalies with explanations
        """
        prompt = f"""
Analyze these HR metrics for anomalies:

Data Points: {json.dumps(data_points, indent=2)}

Identify any unusual patterns, outliers, or concerning trends.
For each anomaly found, provide:
- What is unusual
- Why it matters
- Recommended action

Format as JSON list: [{{"type": "anomaly type", "description": "what's wrong", "severity": "low/medium/high", "action": "what to do"}}]
"""
        
        response_text = self.generate_text(prompt, max_tokens=600, temperature=0.4)
        
        try:
            result = json.loads(response_text)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            return []
    
    def generate_document_content(self, doc_type: str, data: Dict[str, Any]) -> str:
        """
        Generate document content (reports, certificates, letters)
        
        Args:
            doc_type: Type of document (report/certificate/letter)
            data: Data to include in document
            
        Returns:
            Generated document content
        """
        prompts = {
            "performance_report": f"""
Write a professional performance review summary for:

Employee: {data.get('employee_name')}
Period: {data.get('period')}
Overall Score: {data.get('overall_score')}/10
Technical Skills: {data.get('technical_score')}/10
Teamwork: {data.get('teamwork_score')}/10
Productivity: {data.get('productivity_score')}/10
Innovation: {data.get('innovation_score')}/10

Include: summary paragraph, key achievements, areas for development, and future goals.
""",
            "recommendation_letter": f"""
Write a professional recommendation letter for:

Student: {data.get('student_name')}
Project/Internship: {data.get('project_title')}
Supervisor: {data.get('supervisor_name')}
Performance: {data.get('performance_summary')}
Skills Demonstrated: {data.get('skills')}

Make it compelling and specific.
""",
            "certificate": f"""
Write certificate text for:

Recipient: {data.get('recipient_name')}
Achievement: {data.get('achievement')}
Date: {data.get('date')}
Authority: {data.get('issuing_authority')}

Keep it formal and concise (2-3 sentences).
"""
        }
        
        prompt = prompts.get(doc_type, f"Generate professional document content for: {json.dumps(data)}")
        return self.generate_text(prompt, max_tokens=800, temperature=0.6)


class OdooAIService(models.AbstractModel):
    """Odoo model wrapper for AI Service"""
    _name = 'ensa.ai.service'
    _description = 'AI Service Integration'
    
    @api.model
    def get_ai_service(self) -> AIService:
        """Get configured AI service"""
        params = self.env['ir.config_parameter'].sudo()
        
        provider = params.get_param('ensa_hr.ai_provider', 'openai')
        openai_key = params.get_param('ensa_hr.openai_api_key')
        gemini_key = params.get_param('ensa_hr.gemini_api_key')
        huggingface_key = params.get_param('ensa_hr.huggingface_api_key')
        
        model = None
        if provider == 'openai':
            model = params.get_param('ensa_hr.openai_model', 'gpt-4o-mini')
        elif provider == 'gemini':
            model = params.get_param('ensa_hr.gemini_model', 'gemini-flash-latest')
        elif provider == 'huggingface':
            model = params.get_param('ensa_hr.huggingface_model', 'HuggingFaceH4/zephyr-7b-beta')
            
        return AIService(provider, openai_key=openai_key, gemini_key=gemini_key, huggingface_key=huggingface_key, model=model)


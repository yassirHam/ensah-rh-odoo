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
    
    def __init__(self, provider: str = "huggingface", huggingface_key: str = None, bytez_key: str = None, model: str = None):
        """
        Initialize AI Service with provider selection
        """
        self.provider = provider
        self.huggingface_key = huggingface_key
        self.bytez_key = bytez_key
        
        # Default models per provider if not specified
        if not model:
            if provider == "huggingface":
                self.model = "microsoft/Phi-3-mini-4k-instruct"
            elif provider == "bytez":
                self.model = "Qwen/Qwen3-4B-Instruct-2507"
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
            if self.provider == 'huggingface':
                result = self._generate_huggingface(prompt, max_tokens, temperature)
            elif self.provider == 'bytez':
                result = self._generate_bytez(prompt, max_tokens, temperature)
            else:
                raise UserError(_("Unknown AI provider: %s") % self.provider)
            
            # Ensure result is a string
            if not isinstance(result, str):
                result = str(result)
                
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
        
        # Use Hugging Face Router (OpenAI Compatible)
        # This is the modern endpoint for supported models
        api_url = "https://router.huggingface.co/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.huggingface_key}",
            "Content-Type": "application/json"
        }
        
        # The Router requires OpenAI-style 'messages' payload
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,  # Router maps this correctly
            "temperature": max(0.1, temperature),
            "stream": False
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            try:
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    return str(result)
            except (KeyError, IndexError) as e:
                _logger.error(f"Failed to parse Hugging Face response: {result}")
                return str(result)
        else:
             # Handle 503 Model Loading
             if response.status_code == 503:
                 raise UserError("Model is loading (cold boot). Please try again in 30 seconds.")
             
             # Try to extract error message
             error_msg = response.text
             try:
                 error_json = response.json()
                 if 'error' in error_json:
                     # Handle nested error objects
                     if isinstance(error_json['error'], dict):
                         error_msg = error_json['error'].get('message', str(error_json['error']))
                     else:
                         error_msg = error_json['error']
             except:
                 pass
                 
             raise UserError(f"Hugging Face Error: {error_msg}")

    def _generate_bytez(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call Bytez API for Qwen models (Direct HTTP)"""
        if not self.bytez_key:
             raise UserError(_("Bytez API key is missing"))

        try:
            # Direct API call to avoid 'bytez' library dependency issues
            url = f"https://api.bytez.com/models/v2/{self.model}"
            
            headers = {
                "Authorization": f"Key {self.bytez_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "input": [{"role": "user", "content": prompt}],
                "params": {
                    "temperature": max(0.1, temperature),
                    "max_new_tokens": max_tokens
                },
                "stream": False
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('output'):
                    out = result['output']
                    if isinstance(out, (dict, list)):
                        return json.dumps(out)
                    return str(out)
                else:
                    return str(result)
            else:
                 error_msg = response.text
                 try:
                     err_json = response.json()
                     if 'error' in err_json:
                         error_msg = err_json['error']
                 except:
                     pass
                 raise UserError(f"Bytez API Error ({response.status_code}): {error_msg}")

        except Exception as e:
            _logger.error(f"Bytez generation error: {str(e)}")
            raise UserError(f"Bytez Service Error: {str(e)}")

    def answer_query(self, question: str, context_data: Dict[str, Any]) -> str:
        """
        Answer a natural language query about HR data
        
        Args:
            question: The user's question
            context_data: Dictionary containing HR context/stats
            
        Returns:
            AI generated answer
        """
        prompt = f"""
You are an intelligent HR Assistant for ENSA Hoceima. 
Use the following real-time data to answer the user's question accurately.

CONTEXT DATA:
{json.dumps(context_data, indent=2)}

USER QUESTION: 
{question}

INSTRUCTIONS:
- You are analyzing the "Ensa Hoceima HR & Student Management System".
- "HR Module" refers to Employees, Evaluations, and Trainings.
- "Student Module" refers to Internships and Student Projects.
- If asked "Who is the best employee", check the "top_performers" list in the context and answer DIRECTLY with names and scores.
- Do NOT say "it's difficult to say" or "I need more information" if data is present in the context.
- Be precise, technical, and use the provided individual scores.
- **IMPORTANT: Format your response as clean HTML tags (e.g., <p>, <ul>, <li>, <strong>). Do NOT use Markdown (no *, no #).**
- Keep the design clean and minimal.
"""
        return self.generate_text(prompt, max_tokens=500, temperature=0.5)

    def _generate_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Deprecated: OpenAI integration removed"""
        raise UserError(_("OpenAI integration has been removed."))

    def _generate_gemini(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Deprecated: Gemini integration removed"""
        raise UserError(_("Gemini integration has been removed."))
        
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings (Not currently supported without OpenAI)
        """
        # TODO: Implement Hugging Face embeddings
        _logger.warning("Embeddings currently disabled.")
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
- What is unusual (title)
- Why it matters (description)
- Recommended action

Format as JSON list: [{{"title": "...", "description": "...", "severity": "low/medium/high"}}]
"""
        
        _logger.info(f"AI: Sending anomaly detection prompt. Provider: {self.provider}")
        response_text = self.generate_text(prompt, max_tokens=600, temperature=0.4)
        _logger.info(f"AI: Raw anomaly response: {response_text[:200]}...")
        
        try:
            # Clean possible markdown wrap
            clean_json = response_text.strip()
            if clean_json.startswith('```json'): clean_json = clean_json[7:]
            if clean_json.endswith('```'): clean_json = clean_json[:-3]
            
            result = json.loads(clean_json)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError as e:
            _logger.error(f"AI: Anomaly JSON parsing error: {str(e)}")
            return []

    def detect_turnover_risk(self, emp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict turnover risk for an employee using AI
        
        Args:
            emp_data: Dictionary of employee metrics
            
        Returns:
            Dictionary with risk score and mitigation
        """
        # Optimized to use batch_analyze_turnover for multiple employees
        results = self.batch_analyze_turnover([emp_data])
        return results[0] if results else {"risk_score": 0, "risk_level": "low"}

    def batch_analyze_turnover(self, employees_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple employees for turnover risk in a single AI call.
        """
        if not employees_list: return []
        
        prompt = f"""
Analyze the turnover risk for these {len(employees_list)} employees:
{json.dumps(employees_list, indent=2)}

Task: Identify risk factors and calculate a risk score (0-100) for EACH.
Return ONLY a JSON list of objects: [{{"employee_name": "...", "risk_score": integer, "risk_level": "low/medium/high"}}]
"""
        _logger.info(f"AI: Sending batch turnover prompt for {len(employees_list)} emps")
        response_text = self.generate_text(prompt, max_tokens=1000, temperature=0.3)
        _logger.info(f"AI: Raw batch turnover response: {response_text[:200]}...")
        
        try:
            clean_json = response_text.strip()
            if clean_json.startswith('```json'): clean_json = clean_json[7:]
            if clean_json.endswith('```'): clean_json = clean_json[:-3]
            
            result = json.loads(clean_json)
            return result if isinstance(result, list) else []
        except Exception as e:
            _logger.error(f"AI: Batch turnover JSON parsing error: {str(e)}")
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
        bytez_key = params.get_param('ensa_hr.bytez_api_key')
        
        model = None
        if provider == 'openai':
            model = params.get_param('ensa_hr.openai_model', 'gpt-4o-mini')
        elif provider == 'gemini':
            model = params.get_param('ensa_hr.gemini_model', 'gemini-flash-latest')
        elif provider == 'huggingface':
            model = params.get_param('ensa_hr.huggingface_model', 'microsoft/Phi-3-mini-4k-instruct')
        elif provider == 'bytez':
            model = params.get_param('ensa_hr.bytez_model', 'Qwen/Qwen3-4B-Instruct-2507')
            
        return AIService(provider, huggingface_key=huggingface_key, bytez_key=bytez_key, model=model)


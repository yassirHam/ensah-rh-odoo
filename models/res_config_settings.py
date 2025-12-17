from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    openai_api_key = fields.Char(
        string="OpenAI API Key",
        config_parameter='ensa_hr.openai_api_key',
        help="Your OpenAI API key for AI-powered features"
    )

    # AI Provider Selection
    ai_provider = fields.Selection([
        ('openai', 'OpenAI (GPT-4)'),
        ('gemini', 'Google Gemini (Free Tier Available)'),
        ('huggingface', 'Hugging Face (Free Open Source)'),
    ], string="AI Provider",
       config_parameter='ensa_hr.ai_provider',
       default='gemini',
       help="Select the AI service provider")

    # Gemini Configuration
    gemini_api_key = fields.Char(
        string="Gemini API Key",
        config_parameter='ensa_hr.gemini_api_key',
        help="Your Google Gemini API key"
    )
    gemini_model = fields.Selection([
        ('gemini-flash-latest', 'Gemini Flash (Latest)'),
        ('gemini-pro-latest', 'Gemini Pro (Latest)'),
        ('gemini-2.5-flash', 'Gemini 2.5 Flash'),
        ('gemini-2.5-pro', 'Gemini 2.5 Pro'),
        ('gemini-2.0-flash', 'Gemini 2.0 Flash'),
        # Legacy/Deprecated mappings
        ('gemini-1.5-flash-latest', 'Gemini 1.5 Flash (Deprecated)'),
        ('gemini-1.5-pro-latest', 'Gemini 1.5 Pro (Deprecated)'),
        ('gemini-pro', 'Gemini 1.0 Pro (Deprecated)'),
        ('gemini-1.5-flash', 'Gemini 1.5 Flash (Legacy)'),
    ], string="Gemini Model",
       config_parameter='ensa_hr.gemini_model',
       default='gemini-flash-latest',
       help="Choose the Gemini model to use")

    openai_model = fields.Selection([
        ('gpt-4o', 'GPT-4o (Latest, Best)'),
        ('gpt-4o-mini', 'GPT-4o Mini (Fast, Cheap)'),
        ('gpt-4', 'GPT-4 (Legacy)'),
        ('gpt-4-turbo-preview', 'GPT-4 Turbo'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
    ], string="AI Model", 
       config_parameter='ensa_hr.openai_model',
       default='gpt-4o-mini',
       help="Choose the OpenAI model to use")
       
    # Hugging Face Configuration
    huggingface_api_key = fields.Char(
        string="Hugging Face Token",
        config_parameter='ensa_hr.huggingface_api_key',
        help="Access Token from huggingface.co/settings/tokens"
    )
    huggingface_model = fields.Selection([
        ('google/gemma-2-2b-it', 'Google Gemma 2 2B (Fast, Recommended)'),
        ('Qwen/Qwen2.5-1.5B-Instruct', 'Qwen 2.5 1.5B (Lightweight)'),
        ('mistralai/Mistral-7B-Instruct-v0.2', 'Mistral 7B (High Quality)'),
    ], string="Hugging Face Model",
       config_parameter='ensa_hr.huggingface_model',
       default="google/gemma-2-2b-it",
       help="Select a free Hugging Face model. All models work without credit card."
    )
    
    enable_ai_features = fields.Boolean(
        string="Enable AI Features",
        config_parameter='ensa_hr.enable_ai_features',
        default=True,
        help="Enable AI-powered insights, predictions, and analysis"
    )
    
    # Twilio WhatsApp Configuration
    twilio_account_sid = fields.Char(
        string="Twilio Account SID",
        config_parameter='ensa_hr.twilio_account_sid',
        help="Your Twilio Account SID"
    )
    twilio_auth_token = fields.Char(
        string="Twilio Auth Token",
        config_parameter='ensa_hr.twilio_auth_token',
        help="Your Twilio Auth Token"
    )
    twilio_whatsapp_number = fields.Char(
        string="WhatsApp Business Number",
        config_parameter='ensa_hr.twilio_whatsapp_number',
        default='whatsapp:+14155238886',
        help="Your WhatsApp Business number (format: whatsapp:+1234567890)"
    )
    
    enable_whatsapp_bot = fields.Boolean(
        string="Enable WhatsApp Bot",
        config_parameter='ensa_hr.enable_whatsapp_bot',
        default=True,
        help="Enable WhatsApp chatbot for employee self-service"
    )
    
    # Matching Engine Configuration
    enable_smart_matching = fields.Boolean(
        string="Enable Smart Matching",
        config_parameter='ensa_hr.enable_smart_matching',
        default=True,
        help="Enable AI-powered internship and project matching"
    )
    
    matching_threshold = fields.Integer(
        string="Minimum Match Score",
        config_parameter='ensa_hr.matching_threshold',
        default=50,
        help="Minimum match score (0-100) to show suggestions"
    )
    
    # Document Generation Configuration
    enable_auto_documents = fields.Boolean(
        string="Enable Auto-Document Generation",
        config_parameter='ensa_hr.enable_auto_documents',
        default=True,
        help="Automatically generate PDFs for evaluations and certificates"
    )
    
    # Feature Flags
    enable_turnover_prediction = fields.Boolean(
        string="Enable Turnover Prediction",
        config_parameter='ensa_hr.enable_turnover_prediction',
        default=True,
        help="Predict employee turnover risk using AI"
    )
    
    enable_internship_tracking = fields.Boolean(
        string="Enable Internship Progress Tracking",
        config_parameter='ensa_hr.enable_internship_tracking',
        default=True,
        help="Track internship progress via WhatsApp check-ins"
    )
    
    # API Usage Stats
    api_calls_this_month = fields.Integer(
        string="API Calls This Month",
        compute='_compute_api_stats',
        help="Number of AI API calls made this month"
    )
    
    estimated_cost = fields.Float(
        string="Estimated Cost ($)",
        compute='_compute_api_stats',
        help="Estimated API costs this month"
    )
    
    def _compute_api_stats(self):
        """Compute API usage statistics"""
        for record in self:
            # TODO: Implement actual tracking
            record.api_calls_this_month = 0
            record.estimated_cost = 0.0
    
    def action_test_ai_connection(self):
        """Test AI Provider API connection"""
        self.ensure_one()
        
        provider = self.ai_provider or 'openai'
        
        try:
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            
            # Simple ping message
            test_response = ai_service.generate_text(
                "Reply with 'Connection Successful'",
                max_tokens=20,
                temperature=0
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Successful'),
                    'message': f"Connected to {dict(self._fields['ai_provider'].selection).get(provider)}: {test_response}",
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            raise UserError(_("Connection failed: %s") % str(e))
    
    def action_test_whatsapp_connection(self):
        """Test Twilio WhatsApp connection"""
        self.ensure_one()
        
        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_whatsapp_number]):
            raise UserError(_("Please complete all Twilio configuration fields."))
        
        try:
            whatsapp_service = self.env['ensa.whatsapp.service'].get_whatsapp_service()
            
            # Try to get account info (this validates credentials) via direct API
            import requests
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}.json"
            response = requests.get(
                url,
                auth=(self.twilio_account_sid, self.twilio_auth_token),
                timeout=10
            )
            
            if response.status_code == 200:
                account_data = response.json()
                friendly_name = account_data.get('friendly_name', 'Twilio Account')
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Successful'),
                        'message': f"Connected to Twilio account: {friendly_name}",
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_("Twilio API error: %s") % response.text)
                
        except Exception as e:
            raise UserError(_("Connection failed: %s") % str(e))

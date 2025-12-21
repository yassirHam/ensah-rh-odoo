from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # AI Provider Selection
    ai_provider = fields.Selection([
        ('huggingface', 'Hugging Face (Free Open Source)'),
        ('bytez', 'Bytez (Qwen Models)'),
        # Deprecated
        ('openai', 'OpenAI (Deprecated)'),
        ('gemini', 'Google Gemini (Deprecated)'),
    ], string="AI Provider",
       config_parameter='ensa_hr.ai_provider',
       default='huggingface',
       help="Select the AI service provider")

    # Hugging Face Configuration
       
    # Hugging Face Configuration
    huggingface_api_key = fields.Char(
        string="Hugging Face Token",
        config_parameter='ensa_hr.huggingface_api_key',
        help="Access Token from huggingface.co/settings/tokens"
    )
    huggingface_model = fields.Selection([
        ('microsoft/Phi-3-mini-4k-instruct', 'Microsoft Phi-3 Mini 4k (Instruct)'),
        # Legacy models (kept for compatibility)
        ('google/gemma-2-2b-it', 'Google Gemma 2 2B (Deprecated)'),
        ('Qwen/Qwen2.5-1.5B-Instruct', 'Qwen 2.5 1.5B (Deprecated)'),
        ('mistralai/Mistral-7B-Instruct-v0.2', 'Mistral 7B (Deprecated)'),
    ], string="Hugging Face Model",
       config_parameter='ensa_hr.huggingface_model',
       default="microsoft/Phi-3-mini-4k-instruct",
       help="Select a free Hugging Face model. All models work without credit card."
    )

    # Bytez Configuration
    bytez_api_key = fields.Char(
        string="Bytez API Key",
        config_parameter='ensa_hr.bytez_api_key',
        help="Your Bytez API key"
    )
    bytez_model = fields.Selection([
        ('Qwen/Qwen3-4B-Instruct-2507', 'Qwen 3 4B Instruct'),
    ], string="Bytez Model",
       config_parameter='ensa_hr.bytez_model',
       default='Qwen/Qwen3-4B-Instruct-2507',
       help="Select the Bytez model")
    
    enable_ai_features = fields.Boolean(
        string="Enable AI Features",
        config_parameter='ensa_hr.enable_ai_features',
        default=True,
        help="Enable AI-powered insights, predictions, and analysis"
    )
    
    
    # WhatsApp Bot (handled by Node.js bridge)
    enable_whatsapp_bot = fields.Boolean(
        string="Enable WhatsApp Bot",
        config_parameter='ensa_hr.enable_whatsapp_bot',
        default=True,
        help="Enable WhatsApp chatbot (requires Node.js bridge)"
    )
    
    # Test Field (Stored in system parameters)
    test_whatsapp_number = fields.Char(
        string="Test Phone Number", 
        config_parameter='ensa_hr.test_whatsapp_number',
        help="Format: +212612345678"
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
        
        provider = self.ai_provider or 'huggingface'
        
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

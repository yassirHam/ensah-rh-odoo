from odoo import models, fields, api, _


class InternshipCheckin(models.Model):
    _name = 'ensa.internship.checkin'
    _description = 'Internship Progress Check-in'
    _order = 'checkin_date desc'
    
    internship_id = fields.Many2one('ensa.internship', string="Internship", required=True, ondelete='cascade')
    student_name = fields.Char(related='internship_id.student_name', string="Student", readonly=True, store=True)
    company_name = fields.Char(related='internship_id.host_company', string="Company", readonly=True, store=True)
    
    checkin_date = fields.Date(string="Check-in Date", default=fields.Date.context_today, required=True)
    message = fields.Text(string="Progress Update", required=True, help="Student's progress update")
    
    # AI Analysis
    sentiment = fields.Selection([
        ('positive', '✅ Positive'),
        ('neutral', '➖ Neutral'),
        ('concerning', '⚠️ Concerning')
    ], string="Sentiment", compute='_compute_sentiment', store=True, help="AI-detected sentiment")
    
    detected_keywords = fields.Char(string="Keywords", compute='_compute_sentiment', store=True)
    ai_summary = fields.Text(string="AI Summary", compute='_compute_sentiment', store=True)
    
    # Flagging
    requires_attention = fields.Boolean(string="Requires Attention", compute='_compute_sentiment', store=True)
    supervisor_notified = fields.Boolean(string="Supervisor Notified", default=False)
    
    # Source tracking
    source = fields.Selection([
        ('whatsapp', 'WhatsApp'),
        ('manual', 'Manual Entry'),
        ('email', 'Email')
    ], string="Source", default='manual')
    
    @api.depends('message')
    def _compute_sentiment(self):
        """Use AI to analyze check-in message sentiment"""
        for checkin in self:
            if not checkin.message:
                checkin.sentiment = 'neutral'
                checkin.detected_keywords = ''
                checkin.ai_summary = ''
                checkin.requires_attention = False
                continue
            
            # Check if AI is enabled
            if self.env['ir.config_parameter'].sudo().get_param('ensa_hr.enable_ai_features', 'True') != 'True':
                # Simple keyword detection fallback
                message_lower = checkin.message.lower()
                concerning_keywords = ['struggling', 'difficult', 'problem', 'issue', 'help', 'confused', 'stuck', 'challenge']
                
                if any(keyword in message_lower for keyword in concerning_keywords):
                    checkin.sentiment = 'concerning'
                    checkin.requires_attention = True
                else:
                    checkin.sentiment = 'positive'
                    checkin.requires_attention = False
                continue
            
            # Use AI for sentiment analysis
            try:
                ai_service = self.env['ensa.ai.service'].get_ai_service()
                
                prompt = f"""Analyze this internship progress check-in:

"{checkin.message}"

Provide:
1. Sentiment: positive/neutral/concerning
2. Key topics (comma-separated keywords)
3. One-line summary
4. Does it require supervisor attention? (yes/no)

Format as JSON: {{"sentiment": "...", "keywords": "...", "summary": "...", "attention_needed": true/false}}"""
                
                response = ai_service.generate_text(prompt, max_tokens=200, temperature=0.2)
                
                import json
                try:
                    analysis = json.loads(response)
                    checkin.sentiment = analysis.get('sentiment', 'neutral')
                    checkin.detected_keywords = analysis.get('keywords', '')
                    checkin.ai_summary = analysis.get('summary', '')
                    checkin.requires_attention = analysis.get('attention_needed', False)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    if 'concerning' in response.lower() or 'negative' in response.lower():
                        checkin.sentiment = 'concerning'
                        checkin.requires_attention = True
                    else:
                        checkin.sentiment = 'positive'
                        checkin.requires_attention = False
                        
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Sentiment analysis failed: {str(e)}")
                checkin.sentiment = 'neutral'
                checkin.requires_attention = False
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to trigger supervisor notification if needed"""
        records = super(InternshipCheckin, self).create(vals_list)
        
        for record in records:
            if record.requires_attention and not record.supervisor_notified:
                record._notify_supervisor()
        
        return records
    
    def _notify_supervisor(self):
        """Notify supervisor if check-in requires attention"""
        self.ensure_one()
        
        if not self.internship_id.supervisor_id or not self.internship_id.supervisor_id.user_id:
            return
        
        try:
            # Create activity for supervisor
            self.internship_id.activity_schedule(
                'mail.mail_activity_data_warning',
                summary=f"Student Check-in Requires Attention - {self.student_name}",
                note=f"""Student check-in indicates potential issues:

**Check-in Message:**
{self.message}

**AI Analysis:**
Sentiment: {dict(self._fields['sentiment'].selection).get(self.sentiment)}
Keywords: {self.detected_keywords}
Summary: {self.ai_summary}

Please follow up with the student promptly.""",
                user_id=self.internship_id.supervisor_id.user_id.id
            )
            
            # Try to send WhatsApp notification if enabled
            if self.env['ir.config_parameter'].sudo().get_param('ensa_hr.enable_whatsapp_bot', 'True') == 'True':
                # Will implement WhatsApp notification later
                pass
            
            self.supervisor_notified = True
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Supervisor notification failed: {str(e)}")

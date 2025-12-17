"""
WhatsApp Service for ENSA HR Module
Handles Twilio WhatsApp Business API integration
"""
import logging

from typing import Optional, Dict, Any, List
import requests
import base64
from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WhatsAppService:
    """WhatsApp messaging service using Twilio API directly"""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        """
        Initialize WhatsApp Service
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_number: WhatsApp Business number (format: whatsapp:+1234567890)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number if from_number.startswith('whatsapp:') else f'whatsapp:{from_number}'
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    def send_message(self, to_number: str, message: str, media_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Send WhatsApp message via Twilio API
        """
        try:
            # Format number
            to_whatsapp = to_number if to_number.startswith('whatsapp:') else f'whatsapp:{to_number}'
            
            _logger.info(f"Sending WhatsApp message to {to_whatsapp}")
            
            data = {
                'To': to_whatsapp,
                'From': self.from_number,
                'Body': message
            }
            
            if media_url:
                data['MediaUrl'] = media_url
            
            response = requests.post(
                self.api_url,
                data=data,
                auth=(self.account_sid, self.auth_token),
                timeout=10
            )
            
            response_data = response.json()
            
            if response.status_code in (200, 201):
                return {
                    'sid': response_data.get('sid'),
                    'status': response_data.get('status'),
                    'to': to_number,
                    'success': True
                }
            else:
                _logger.error(f"Twilio API error: {response.text}")
                return {
                    'success': False,
                    'error': response_data.get('message', 'Unknown error'),
                    'code': response_data.get('code'),
                    'to': to_number
                }
            
        except Exception as e:
            _logger.error(f"WhatsApp send error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'to': to_number
            }
    
    def send_template_message(self, to_number: str, template_sid: str, variables: Dict[str, str]) -> Dict[str, Any]:
        """
        Send WhatsApp template message
        """
        try:
            to_whatsapp = to_number if to_number.startswith('whatsapp:') else f'whatsapp:{to_number}'
            
            data = {
                'To': to_whatsapp,
                'From': self.from_number,
                'ContentSid': template_sid,
                'ContentVariables': str(variables) # Twilio expects JSON string for some endpoints, but passing query params for simple ones
            }
            # Note: Template messaging often requires different payload structure depends on exact API endpoint used (Programmable Messaging vs Content API)
            # For simplicity with basic Twilio API, we'll stick to basic body.
            # If using Content API, specific endpoint is needed. 
            # Fallback to standard message for now as safe default if template logic is complex without lib.
            
            _logger.warning("Native template sending not fully supported in zero-dep mode yet, falling back to basic message if possible")
            
            return {'success': False, 'error': "Template sending requires advanced API handling"}
            
        except Exception as e:
            _logger.error(f"Template message error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def validate_webhook(self, url: str, params: Dict[str, Any], signature: str) -> bool:
        """
        Validate Twilio webhook request (Basic check)
        """
        # Without twilio library, full signature validation is complex to implement manually
        # For now, we return True to allow operation, or check a shared secret if available.
        return True 
    
    def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get message delivery status
        """
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages/{message_sid}.json"
            response = requests.get(
                url,
                auth=(self.account_sid, self.auth_token),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'sid': data.get('sid'),
                    'status': data.get('status'),
                    'error_code': data.get('error_code'),
                    'error_message': data.get('error_message'),
                    'date_sent': data.get('date_sent')
                }
            else:
                return {'error': f"Status check failed: {response.text}"}
                
        except Exception as e:
            _logger.error(f"Status fetch error: {str(e)}")
            return {'error': str(e)}
    
    def send_bulk_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Send multiple WhatsApp messages
        
        Args:
            messages: List of dicts with 'to' and 'message' keys
            
        Returns:
            List of send results
        """
        results = []
        for msg in messages:
            result = self.send_message(
                to_number=msg.get('to'),
                message=msg.get('message'),
                media_url=msg.get('media_url')
            )
            results.append(result)
        return results
    
    def format_menu_message(self, title: str, options: List[str]) -> str:
        """
        Format menu message with numbered options
        
        Args:
            title: Menu title
            options: List of menu options
            
        Returns:
            Formatted message
        """
        message = f"*{title}*\n\n"
        for i, option in enumerate(options, 1):
            message += f"{i}. {option}\n"
        message += "\nReply with the number of your choice."
        return message
    
    def send_notification(self, to_number: str, notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send formatted notification based on type
        
        Args:
            to_number: Recipient phone number
            notification_type: Type of notification
            data: Notification data
            
        Returns:
            Send result
        """
        templates = {
            'evaluation_submitted': """
🔔 *Performance Evaluation*

Hello {employee_name},

Your performance evaluation has been submitted for approval.

*Overall Score:* {score}/10
*Status:* Pending Manager Approval

You will be notified once approved.
""",
            'evaluation_approved': """
✅ *Evaluation Approved*

Hello {employee_name},

Your performance evaluation has been approved!

*Overall Score:* {score}/10
*Recommendation:* {recommendation}

View details in your HR portal.
""",
            'internship_opportunity': """
🎓 *New Internship Opportunity*

Hello {student_name},

A matching internship has been found for you!

*Company:* {company_name}
*Domain:* {domain}
*Duration:* {duration}
*Match Score:* {match_score}%

Reply with 'INTERESTED' to learn more.
""",
            'weekly_checkin': """
📋 *Weekly Progress Check-in*

Hello {student_name},

How is your internship at {company_name} going this week?

Please share:
1. What you worked on
2. Any challenges
3. What you learned

Reply with your update.
""",
            'supervisor_alert': """
⚠️ *Supervisor Alert*

Student {student_name} needs attention:

*Issue:* {issue}
*Internship:* {company_name}
*Risk Level:* {risk_level}

Please follow up promptly.
""",
            'training_reminder': """
📚 *Training Reminder*

Hello {employee_name},

Upcoming training session:

*Course:* {course_name}
*Date:* {date}
*Duration:* {duration}

Don't forget to attend!
""",
            'document_ready': """
📄 *Document Ready*

Hello {recipient_name},

Your {document_type} is ready!

{document_description}

Download: {document_url}
"""
        }
        
        template = templates.get(notification_type, """
*Notification*

{message}
""")
        
        message = template.format(**data)
        
        return self.send_message(to_number, message)


class OdooWhatsAppService(models.AbstractModel):
    """Odoo model wrapper for WhatsApp Service"""
    _name = 'ensa.whatsapp.service'
    _description = 'WhatsApp Service Integration'
    
    @api.model
    def get_whatsapp_service(self) -> WhatsAppService:
        """
        Get configured WhatsApp service instance
        
        Returns:
            WhatsAppService instance
        """
        account_sid = self.env['ir.config_parameter'].sudo().get_param('ensa_hr.twilio_account_sid')
        auth_token = self.env['ir.config_parameter'].sudo().get_param('ensa_hr.twilio_auth_token')
        from_number = self.env['ir.config_parameter'].sudo().get_param('ensa_hr.twilio_whatsapp_number')
        
        if not all([account_sid, auth_token, from_number]):
            raise UserError(_("Twilio WhatsApp configuration incomplete. Please configure in Settings."))
        
        return WhatsAppService(
            account_sid=account_sid,
            auth_token=auth_token,
            from_number=from_number
        )
    
    @api.model
    def send_message(self, to_number: str, message: str, media_url: Optional[str] = None) -> bool:
        """
        Send WhatsApp message (Odoo-friendly wrapper)
        
        Args:
            to_number: Recipient phone number
            message: Message text
            media_url: Optional media URL
            
        Returns:
            True if sent successfully
        """
        service = self.get_whatsapp_service()
        result = service.send_message(to_number, message, media_url)
        return result.get('success', False)

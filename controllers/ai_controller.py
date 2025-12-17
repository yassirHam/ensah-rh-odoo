from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class AIController(http.Controller):
    
    @http.route('/ensa_hr/ai/chat', type='json', auth='user')
    def chat(self, question, **kwargs):
        """Chat endpoint for AI assistant"""
        try:
            ai_assistant = request.env['ensa.ai.assistant']
            result = ai_assistant.ask_question(question)
            return result
        except Exception as e:
            _logger.error(f"Chat endpoint error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/ensa_hr/ai/history', type='json', auth='user')
    def get_history(self, limit=20, **kwargs):
        """Get chat history for current user"""
        try:
            chats = request.env['ensa.ai.assistant'].search(
                [('user_id', '=', request.env.user.id)],
                order='create_date desc',
                limit=limit
            )
            
            return {
                'success': True,
                'chats': [{
                    'id': chat.id,
                    'question': chat.question,
                    'answer': chat.answer,
                    'timestamp': chat.create_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'response_time': chat.response_time
                } for chat in chats]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/ensa_hr/ai/suggestions', type='json', auth='user')
    def get_suggestions(self, **kwargs):
        """Get AI-powered visualization/analysis suggestions"""
        try:
            ai_assistant = request.env['ensa.ai.assistant']
            result = ai_assistant.get_suggestions()
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/ensa_hr/ai/predictions', type='json', auth='user')
    def get_predictions(self, **kwargs):
        """Get AI-powered future trend predictions"""
        try:
            ai_assistant = request.env['ensa.ai.assistant']
            result = ai_assistant.predict_future_trends()
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/ensa_hr/ai/dashboard_insights', type='json', auth='user')
    def get_dashboard_insights(self, **kwargs):
        """Get AI insights for dashboard"""
        try:
            dashboard = request.env['ensa.dashboard']
            dashboard_data = dashboard.get_dashboard_data()
            
            return {
                'success': True,
                'insights': dashboard_data.get('ai_insights', ''),
                'turnover_risks': dashboard_data.get('turnover_risks', []),
                'anomalies': dashboard_data.get('anomalies', [])
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

from odoo import models, fields, api
from datetime import datetime

class AIAssistant(models.Model):
    _name = 'ensa.ai.assistant'
    _description = 'AI Chat Assistant'
    _order = 'create_date desc'
    _rec_name = 'question'
    
    question = fields.Text(string="Question", required=True)
    answer = fields.Html(string="Answer", readonly=True)
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user, readonly=True)
    create_date = fields.Datetime(string="Asked On", readonly=True)
    response_time = fields.Float(string="Response Time (s)", readonly=True)
    token_count = fields.Integer(string="Tokens Used", readonly=True)
    context_data = fields.Text(string="Context Data", readonly=True)
    
    @api.model
    def ask_question(self, question):
        """Main method to ask AI a question about HR data"""
        start_time = datetime.now()
        
        try:
            # Get comprehensive HR context
            context = self._gather_hr_context()
            
            # Query AI service
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            answer = ai_service.answer_query(question, context)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Format answer as HTML
            formatted_answer = self._format_answer(answer)
            
            # Save chat history
            chat_record = self.create({
                'question': question,
                'answer': formatted_answer,
                'response_time': response_time,
                'context_data': str(context)[:500]  # Truncate for storage
            })
            
            return {
                'success': True,
                'id': chat_record.id,
                'question': question,
                'answer': formatted_answer,
                'response_time': response_time,
                'timestamp': chat_record.create_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"AI Assistant error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'question': question
            }
    
    def _gather_hr_context(self):
        """Gather comprehensive HR data for AI context"""
        Employee = self.env['hr.employee']
        Evaluation = self.env['ensa.evaluation']
        Training = self.env['ensa.training']
        
        employees = Employee.search([('active', '=', True)])
        evaluations = Evaluation.search([('state', '=', 'completed')])
        trainings = Training.search([])
        
        # Calculate key metrics
        avg_performance = sum(evaluations.mapped('overall_score')) / len(evaluations) if evaluations else 0
        
        # Department breakdown
        departments = {}
        for emp in employees:
            dept = emp.department_id.name if emp.department_id else 'Undefined'
            departments[dept] = departments.get(dept, 0) + 1
        
        return {
            'total_employees': len(employees),
            'avg_performance': round(avg_performance, 2),
            'departments': departments,
            'total_evaluations': len(evaluations),
            'completed_trainings': len(trainings.filtered(lambda t: t.status == 'completed')),
            'active_internships': self.env['ensa.internship'].search_count([('status', '=', 'in_progress')]) if 'ensa.internship' in self.env else 0,
            'recent_hires': len(employees.filtered(lambda e: e.first_contract_date and (fields.Date.today() - e.first_contract_date).days <= 90)),
            'extra': {
                'evaluation_distribution': self._get_eval_distribution(evaluations),
                'top_performers': self._get_top_performers(employees, evaluations),
                'training_categories': list(set(trainings.mapped('category')))
            }
        }
    
    def _get_eval_distribution(self, evaluations):
        """Get evaluation score distribution"""
        dist = {'excellent': 0, 'good': 0, 'average': 0, 'poor': 0}
        for ev in evaluations:
            if ev.overall_score >= 8.5:
                dist['excellent'] += 1
            elif ev.overall_score >= 7.0:
                dist['good'] += 1
            elif ev.overall_score >= 5.0:
                dist['average'] += 1
            else:
                dist['poor'] += 1
        return dist
    
    def _get_top_performers(self, employees, evaluations):
        """Get list of top performing employees"""
        top = []
        for emp in employees[:10]:  # Limit to avoid too much data
            emp_evals = evaluations.filtered(lambda e: e.employee_id == emp)
            if emp_evals:
                avg = sum(emp_evals.mapped('overall_score')) / len(emp_evals)
                if avg >= 8.0:
                    top.append(emp.name)
        return top[:5]
    
    def _format_answer(self, answer):
        """Format AI answer as beautiful HTML"""
        return f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <div style="color: #2c3e50; line-height: 1.6;">
                {answer}
            </div>
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d;">
                <i class="fa fa-robot"></i> Powered by AI • Generated: {fields.Datetime.now().strftime('%H:%M:%S')}
            </div>
        </div>
        """
    
    @api.model
    def get_suggestions(self):
        """Get AI-powered suggestions for what to visualize or analyze"""
        try:
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            context = self._gather_hr_context()
            
            prompt = f"""Based on this HR data, suggest 3 insightful analyses or visualizations:
            
Total Employees: {context['total_employees']}
Average Performance: {context['avg_performance']}/10
Departments: {list(context['departments'].keys())}

Format as JSON array: [{{"title": "...", "description": "...", "chart_type": "bar/line/pie"}}]"""
            
            suggestions_json = ai_service.generate_text(prompt, max_tokens=300, temperature=0.7)
            
            return {
                'success': True,
                'suggestions': suggestions_json
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @api.model
    def predict_future_trends(self):
        """Predict future HR trends using AI"""
        try:
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            
            # Get historical data
            evaluations = self.env['ensa.evaluation'].search([('state', '=', 'completed')], order='date desc', limit=50)
            
            prompt = f"""Analyze these recent evaluation scores and predict trends for the next 3 months:
            
Recent Scores: {[e.overall_score for e in evaluations[:10]]}
Average: {sum(evaluations.mapped('overall_score'))/len(evaluations) if evaluations else 0:.1f}

Provide:
1. Predicted average score for next quarter
2. Key factors affecting performance
3. Recommendations to improve trends

Format as HTML with headings."""
            
            prediction = ai_service.generate_text(prompt, max_tokens=500, temperature=0.5)
            
            return {
                'success': True,
                'prediction': prediction
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

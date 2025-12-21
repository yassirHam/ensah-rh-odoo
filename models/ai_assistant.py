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
            
    def action_submit_query(self):
        """Action for UI button to submit question"""
        self.ensure_one()
        if not self.question:
            return
            
        try:
            # Gather context AND answer question in one go (in-place)
            start_time = datetime.now()
            context = self._gather_hr_context()
            
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            answer = ai_service.answer_query(self.question, context)
            
            response_time = (datetime.now() - start_time).total_seconds()
            formatted_answer = self._format_answer(answer)
            
            # Update THIS record
            self.write({
                'answer': formatted_answer,
                'response_time': response_time,
                'context_data': str(context)[:500]
            })
            
            # Return action to reload/keep form open
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'ensa.ai.assistant',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'current',
            }
        except Exception as e:
            self.write({
                'answer': f"<p style='color:red'>Error: {str(e)}</p>"
            })
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'ensa.ai.assistant',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'current',
            }
    
    def _gather_hr_context(self):
        """Gather comprehensive HR data for AI context"""
        Employee = self.env['hr.employee']
        Evaluation = self.env['ensa.evaluation']
        Training = self.env['ensa.training']
        
        # Filter for ENSAH employees
        employees = Employee.search([
            ('active', '=', True),
            ('company_id.name', 'ilike', 'ENSA')
        ])
        if not employees:
             employees = Employee.search([('active', '=', True)])
        evaluations = Evaluation.search([('state', '=', 'completed')])
        trainings = Training.search([])
        internships = self.env['ensa.internship'].search([])
        projects = self.env['ensa.student.project'].search([])
        equipment = self.env['ensa.equipment'].search([]) if 'ensa.equipment' in self.env else self.env['ensa.equipment']
        
        # Calculate key metrics
        avg_performance = sum(evaluations.mapped('overall_score')) / len(evaluations) if evaluations else 0
        
        # Department breakdown
        departments = {}
        for emp in employees:
            dept = emp.department_id.name if emp.department_id else 'Undefined'
            departments[dept] = departments.get(dept, 0) + 1
        
        return {
            'HR_Module': {
                'total_employees': len(employees),
                'active_employees_ensa': len(employees),
                'avg_performance_score': round(avg_performance, 2),
                'total_evaluations': len(evaluations),
                'top_performers': self._get_individual_performance(employees, evaluations),
                'training_programs': {
                    'total': len(trainings),
                    'completed': len(trainings.filtered(lambda t: t.status == 'completed'))
                },
                'departments_distribution': departments,
                'equipment_status': {
                    'total_assigned': len(equipment.filtered(lambda e: e.state == 'assigned')),
                    'available': len(equipment.filtered(lambda e: e.state == 'available'))
                }
            },
            'Student_Module': {
                'internships': {
                    'active': len(internships.filtered(lambda i: i.status == 'in_progress')),
                    'total': len(internships),
                    'success_rate': round(sum(internships.mapped('success_probability')) / len(internships) * 100, 1) if internships else 0
                },
                'student_projects': {
                    'active': len(projects.filtered(lambda p: p.status == 'in_progress')),
                    'total': len(projects),
                    'common_technologies': self._get_common_tech(projects)
                }
            },
            'Last_Updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _get_status_counts(self, records):
        """Helper to count records by status"""
        counts = {}
        for r in records:
            s = r.status if 'status' in r else 'unknown'
            counts[s] = counts.get(s, 0) + 1
        return counts

    def _get_common_tech(self, projects):
        """Extract common technologies from projects"""
        techs = {}
        for p in projects:
            if p.technology_stack:
                for t in p.technology_stack.split(','):
                    t = t.strip()
                    techs[t] = techs.get(t, 0) + 1
        # Return top 5
        return dict(sorted(techs.items(), key=lambda item: item[1], reverse=True)[:5])
    
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
    
    def _get_individual_performance(self, employees, evaluations):
        """Get individual scores for top employees"""
        perf = []
        for emp in employees:
            emp_evals = evaluations.filtered(lambda e: e.employee_id == emp)
            if emp_evals:
                latest = emp_evals.sorted('date', reverse=True)[0]
                perf.append({
                    'name': emp.name,
                    'last_score': latest.overall_score,
                    'department': emp.department_id.name or 'N/A'
                })
        # Sort and return top 10
        return sorted(perf, key=lambda x: x['last_score'], reverse=True)[:10]

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
        """Format AI answer as readable HTML"""
        # We now request HTML directly from AI, so we just wrap it
        return f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="color: #2c3e50; line-height: 1.8; font-size: 14px;">
                {answer}
            </div>
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d;">
                <i class="fa fa-robot"></i> AI Response • Generated: {fields.Datetime.now().strftime('%H:%M:%S')}
            </div>
        </div>
        """
    
    @api.model
    def get_suggestions(self):
        """Get AI-powered suggestions for what to visualize or analyze"""
        try:
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            context = self._gather_hr_context()
            
            prompt = f"""You are an HR Analyst. Below is the REAL dataset you must analyze.
Do not ask for data. It is right here:

Total Employees: {context['total_employees']}
Average Performance: {context['avg_performance']}/10
Departments: {list(context['departments'].keys())}

Task: Based on these numbers, suggest 3 insightful analyses or charts we should create.
Format: Return ONLY a JSON array: [{{"title": "...", "description": "...", "chart_type": "bar/line/pie"}}]"""
            
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
            
            prompt = f"""You are an HR Data Analyst. specific data is provided below. 
You must analyze this data and generate a trend prediction.
DO NOT ask for more information. Use ONLY the data provided here.

Recent Evaluation Scores: {[e.overall_score for e in evaluations[:10]]}
Average Score: {sum(evaluations.mapped('overall_score'))/len(evaluations) if evaluations else 0:.1f}

Task:
1. Predict the average score for the next quarter based on the recent scores.
2. Identify key factors affecting performance based on the specific scores above.
3. Provide concrete recommendations to improve trends.

Output Format:
Return your analysis as clean HTML with <h3> headings. Do not include introductory text like "Sure, here is..."."""
            
            prediction = ai_service.generate_text(prompt, max_tokens=500, temperature=0.5)
            
            return {
                'success': True,
                'prediction': prediction
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

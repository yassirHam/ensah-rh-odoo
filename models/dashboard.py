from odoo import models, fields, api
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class HRDashboard(models.TransientModel):
    _name = 'ensa.dashboard'
    _description = 'HR Dashboard Data'

    name = fields.Char(default="HR Analytics Dashboard")
    
    # KPIs
    total_employees = fields.Integer(string="Total Employees", readonly=True)
    avg_performance = fields.Float(string="Avg Performance", digits=(16, 1), readonly=True)
    active_trainings = fields.Integer(string="Active Trainings", readonly=True)
    total_evaluations = fields.Integer(string="Evaluations", readonly=True)
    
    # HTML Content Fields
    ai_insights_html = fields.Html(string="AI Insights", readonly=True, default="<p>Click Refresh to load AI insights...</p>")
    turnover_risks_html = fields.Html(string="Turnover Risks", readonly=True)
    anomalies_html = fields.Html(string="Anomalies", readonly=True)
    predictions_html = fields.Html(string="Predictions", readonly=True)
    suggestions_html = fields.Html(string="Suggestions", readonly=True)
    
    @api.model
    def action_open_dashboard(self):
        """Server action to open dashboard, creating a record if needed"""
        # Create a fresh record for the user
        dashboard = self.create({'name': 'HR Dashboard'})
        
        return {
            'name': 'HR Dashboard',
            'res_model': 'ensa.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'view_id': self.env.ref('ensa_hoceima_hr.view_ensa_dashboard').id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
    
    @api.model
    def get_dashboard_data(self):
        """Simplified dashboard data fetcher with proper error handling"""
        try:
            dashboard_data = {
                'employee_stats': self._get_employee_stats(),
                'evaluation_stats': self._get_evaluation_stats(),
                'equipment_stats': self._get_equipment_stats(),
                'training_stats': self._get_training_stats(),
                'department_distribution': self._get_department_distribution(),
            }
            
            # Add AI-powered insights if enabled
            if self.env['ir.config_parameter'].sudo().get_param('ensa_hr.enable_ai_features', 'True') == 'True':
                dashboard_data['ai_insights'] = self._get_ai_insights(dashboard_data)
                dashboard_data['turnover_risks'] = self._get_turnover_predictions()
                dashboard_data['anomalies'] = self._detect_anomalies(dashboard_data)
            
            return dashboard_data
        except Exception as e:
            _logger.error(f"Dashboard data error: {str(e)}")
            return {}

    def action_refresh(self):
        """Action to refresh dashboard data"""
        data = self.get_dashboard_data()
        
        # Format HTML for lists
        turnover_html = self._format_turnover_list(data.get('turnover_risks', []))
        anomalies_html = self._format_anomalies_list(data.get('anomalies', []))
        
        self.write({
            'total_employees': data.get('employee_stats', {}).get('total', 0),
            'avg_performance': data.get('evaluation_stats', {}).get('avg_score', 0),
            'active_trainings': data.get('training_stats', {}).get('upcoming', 0),
            'total_evaluations': data.get('evaluation_stats', {}).get('total', 0),
            'ai_insights_html': data.get('ai_insights', ''),
            'turnover_risks_html': turnover_html,
            'anomalies_html': anomalies_html
        })
        
        # Keep the wizard open
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ensa.dashboard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _format_turnover_list(self, risks):
        if not risks:
            return "<p class='text-muted'>No high-risk employees detected.</p>"
        
        html = "<ul class='list-group list-group-flush'>"
        for risk in risks:
            html += f"""
            <li class='list-group-item d-flex justify-content-between align-items-center'>
                <div>
                    <span class='font-weight-bold'>{risk['employee_name']}</span>
                    <br/><small class='text-muted'>{risk['mitigation'][:50]}...</small>
                </div>
                <span class='badge badge-danger badge-pill'>{risk['risk_score']}%</span>
            </li>"""
        html += "</ul>"
        return html

    def _format_anomalies_list(self, anomalies):
        if not anomalies:
            return "<p class='text-muted'>No anomalies detected.</p>"
            
        html = "<div class='list-group'>"
        for item in anomalies:
            html += f"""
            <div class='list-group-item list-group-item-action flex-column align-items-start'>
                <div class='d-flex w-100 justify-content-between'>
                    <h6 class='mb-1 text-warning'><i class='fa fa-exclamation-circle'/> {item['title']}</h6>
                </div>
                <p class='mb-1 small'>{item['description']}</p>
            </div>"""
        html += "</div>"
        return html
    
    def action_generate_predictions(self):
        """Generate specific predictions"""
        try:
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            prompt = "Analyze HR trends for the next quarter based on current performance and training data."
            prediction = ai_service.generate_text(prompt, max_tokens=300)
            formatted = f"<div class='alert alert-primary'>{prediction}</div>"
            self.write({'predictions_html': formatted})
        except Exception as e:
             self.write({'predictions_html': f"<div class='alert alert-danger'>Error: {str(e)}</div>"})
        return self.action_refresh()

    def action_get_suggestions(self):
        """Get AI suggestions"""
        try:
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            prompt = "Suggest 3 HR improvements based on current metrics."
            suggestion = ai_service.generate_text(prompt, max_tokens=300)
            formatted = f"<div class='alert alert-success'>{suggestion}</div>"
            self.write({'suggestions_html': formatted})
        except Exception as e:
             self.write({'suggestions_html': f"<div class='alert alert-danger'>Error: {str(e)}</div>"})
        return self.action_refresh()
    
    def _get_employee_stats(self):
        employees = self.env['hr.employee'].search([('active', '=', True)])
        return {
            'total': len(employees),
            'by_department': self._get_count_by_field(employees, 'department_id'),
            'by_skill_level': self._get_count_by_field(employees, 'skill_level'),
            'avg_tenure': self._calculate_avg_tenure(employees),
        }
    
    def _get_evaluation_stats(self):
        evaluations = self.env['ensa.evaluation'].search([('state', '=', 'completed')])
        return {
            'total': len(evaluations),
            'avg_score': sum(evaluations.mapped('overall_score')) / len(evaluations) if evaluations else 0,
            'distribution': self._get_score_distribution(evaluations),
        }
    
    def _get_equipment_stats(self):
        equipment = self.env['ensa.equipment'].search([])
        return {
            'total': len(equipment),
            'by_status': self._get_count_by_field(equipment, 'state'),
        }
    
    def _get_training_stats(self):
        trainings = self.env['ensa.training'].search([('status', '=', 'completed')])
        return {
            'total': len(trainings),
            'by_category': self._get_count_by_field(trainings, 'category'),
            'avg_score': sum(trainings.mapped('post_training_score')) / len(trainings) if trainings else 0,
            'upcoming': len(self.env['ensa.training'].search([
                ('start_date', '>=', fields.Date.today()),
                ('status', '=', 'planned')
            ]))
        }
    
    def _get_department_distribution(self):
        departments = self.env['hr.department'].search([])
        return [{
            'name': dept.name,
            'count': self.env['hr.employee'].search_count([('department_id', '=', dept.id), ('active', '=', True)])
        } for dept in departments]
    
    # Helper methods
    def _get_count_by_field(self, records, field_name):
        results = {}
        for record in records:
            field_value = getattr(record, field_name)
            # Handle both Many2one (has .name) and Selection (is string) fields
            if hasattr(field_value, 'name'):
                key = field_value.name
            elif field_value:
                key = str(field_value)
            else:
                key = 'Undefined'
            results[key] = results.get(key, 0) + 1
        return results
    
    def _get_score_distribution(self, evaluations):
        distribution = {'5-': 0, '5-7': 0, '7-8.5': 0, '8.5+': 0}
        for eval in evaluations:
            score = eval.overall_score
            if score < 5.0:
                distribution['5-'] += 1
            elif 5.0 <= score < 7.0:
                distribution['5-7'] += 1
            elif 7.0 <= score < 8.5:
                distribution['7-8.5'] += 1
            else:
                distribution['8.5+'] += 1
        return distribution
    
    def _calculate_avg_tenure(self, employees):
        total_tenure = 0
        today = fields.Date.today()
        count = 0
        for emp in employees.filtered('first_contract_date'):
            delta = today - emp.first_contract_date
            total_tenure += delta.days / 365.0
            count += 1
        return round(total_tenure / count, 1) if count else 0
    
    # ============ NEW AI-POWERED METHODS ============
    
    @api.model
    def query_dashboard(self, question):
        """Natural language query interface using GPT-4"""
        try:
            if self.env['ir.config_parameter'].sudo().get_param('ensa_hr.enable_ai_features', 'True') != 'True':
                return {'success': False, 'error': 'AI features are disabled'}
            
            # Get dashboard data for context
            dashboard_data = self.get_dashboard_data()
            
            # Prepare context for AI
            context_data = {
                'total_employees': dashboard_data.get('employee_stats', {}).get('total', 0),
                'avg_performance': dashboard_data.get('evaluation_stats', {}).get('avg_score', 0),
                'departments': list(dashboard_data.get('employee_stats', {}).get('by_department', {}).keys()),
                'recent_evaluations': dashboard_data.get('evaluation_stats', {}).get('total', 0),
                'training_programs': dashboard_data.get('training_stats', {}).get('total', 0),
                'active_internships': self.env['ensa.internship'].search_count([('status', '=', 'in_progress')]),
                'active_projects': self.env['ensa.student.project'].search_count([('status', '=', 'in_progress')]),
                'extra': dashboard_data
            }
            
            # Query AI service
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            answer = ai_service.answer_query(question, context_data)
            
            return {
                'success': True,
                'answer': answer,
                'question': question
            }
            
        except Exception as e:
            _logger.error(f"Dashboard query error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _get_ai_insights(self, dashboard_data):
        """Generate AI-powered insights about current HR state"""
        try:
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            
            prompt = f"""Analyze this HR dashboard data and provide 3 key insights:

Total Employees: {dashboard_data.get('employee_stats', {}).get('total', 0)}
Average Performance Score: {dashboard_data.get('evaluation_stats', {}).get('avg_score', 0):.1f}/10
Departments: {list(dashboard_data.get('employee_stats', {}).get('by_department', {}).keys())}
Upcoming Trainings: {dashboard_data.get('training_stats', {}).get('upcoming', 0)}

Provide 3 actionable insights in HTML format.
Format each insight as: <div class="insight"><strong>Title</strong>: Description</div>"""
            
            insights_html = ai_service.generate_text(prompt, max_tokens=400, temperature=0.6)
            return insights_html
            
        except Exception as e:
            _logger.error(f"AI insights error: {str(e)}")
            return "<p>AI insights temporarily unavailable</p>"
    
    def _get_turnover_predictions(self):
        """Predict which employees are at risk of leaving"""
        try:
            if self.env['ir.config_parameter'].sudo().get_param('ensa_hr.enable_turnover_prediction', 'True') != 'True':
                return []
            
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            employees = self.env['hr.employee'].search([('active', '=', True)])
            
            at_risk_employees = []
            
            for emp in employees[:20]:  # Limit to first 20 to avoid too many API calls
                # Prepare employee data
                evaluations = emp.evaluation_ids.sorted('date', reverse=True)[:3]
                recent_scores = [e.overall_score for e in evaluations]
                
                emp_data = {
                    'trend': emp.performance_trend or 'stable',
                    'recent_scores': recent_scores,
                    'avg_score': emp.avg_performance_score,
                    'days_since_eval': (fields.Date.today() - emp.last_evaluation_date).days if emp.last_evaluation_date else 999,
                    'training_count': len(emp.training_ids),
                    'tenure': self._calculate_employee_tenure(emp),
                    'has_certs': len(emp.certification_ids) > 0
                }
                
                # Get AI risk assessment
                risk_assessment = ai_service.detect_turnover_risk(emp_data)
                
                if risk_assessment.get('risk_score', 0) > 60:  # High risk threshold
                    at_risk_employees.append({
                        'employee_id': emp.id,
                        'employee_name': emp.name,
                        'risk_score': risk_assessment.get('risk_score'),
                        'risk_level': risk_assessment.get('risk_level'),
                        'factors': risk_assessment.get('factors', []),
                        'mitigation': risk_assessment.get('mitigation', '')
                    })
            
            return sorted(at_risk_employees, key=lambda x: x['risk_score'], reverse=True)
            
        except Exception as e:
            _logger.error(f"Turnover prediction error: {str(e)}")
            return []
    
    def _detect_anomalies(self, dashboard_data):
        """Detect anomalies in HR metrics using AI"""
        try:
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            
            # Prepare data points for anomaly detection
            data_points = [
                {
                    'metric': 'Average Performance Score',
                    'value': dashboard_data.get('evaluation_stats', {}).get('avg_score', 0),
                    'expected_range': '7.0-8.5'
                },
                {
                    'metric': 'Employee Turnover Rate',
                    'value': self._calculate_turnover_rate(),
                    'expected_range': '5-15%'
                },
                {
                    'metric': 'Training Participation',
                    'value': dashboard_data.get('training_stats', {}).get('total', 0),
                    'employees': dashboard_data.get('employee_stats', {}).get('total', 1)
                }
            ]
            
            anomalies = ai_service.detect_anomalies(data_points)
            return anomalies[:5]  # Top 5 anomalies
            
        except Exception as e:
            _logger.error(f"Anomaly detection error: {str(e)}")
            return []
    
    def _calculate_employee_tenure(self, employee):
        """Calculate tenure for a single employee"""
        if not employee.first_contract_date:
            return 0
        delta = fields.Date.today() - employee.first_contract_date
        return round(delta.days / 365.0, 1)
    
    def _calculate_turnover_rate(self):
        """Calculate employee turnover rate"""
        total_employees = self.env['hr.employee'].search_count([('active', '=', True)])
        # This is a simplified calculation - in production, track actual departures
        # For now, return a placeholder
        return 10.5  # 10.5% placeholder
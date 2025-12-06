from odoo import models, fields, api
from odoo.http import request

class HRDashboard(models.Model):
    _name = 'ensa.dashboard'
    _description = 'HR Dashboard Data'
    _auto = False  # This model won't create a database table

    name = fields.Char()  # Dummy field for ORM compatibility
    
    @api.model
    def get_dashboard_data(self):
        """Simplified dashboard data fetcher with proper error handling"""
        try:
            return {
                'employee_stats': self._get_employee_stats(),
                'evaluation_stats': self._get_evaluation_stats(),
                'equipment_stats': self._get_equipment_stats(),
                'training_stats': self._get_training_stats(),
                'department_distribution': self._get_department_distribution(),
            }
        except Exception as e:
            return {
                'error': str(e),
                'employee_stats': {'total': 0, 'by_department': {}, 'by_skill_level': {}, 'avg_tenure': 0},
                'evaluation_stats': {'total': 0, 'avg_score': 0, 'distribution': {}},
                'equipment_stats': {'total': 0, 'by_status': {}},
                'training_stats': {'total': 0, 'by_category': {}, 'avg_score': 0, 'upcoming': 0},
                'department_distribution': []
            }
    
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
            key = field_value.name if field_value else 'Undefined'
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
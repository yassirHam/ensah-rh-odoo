from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Advanced fields
    identification_number = fields.Char(string="National ID", copy=False)
    emergency_contact = fields.Char(string="Emergency Contact")
    certification_ids = fields.One2many('ensa.employee.certification', 'employee_id', string="Certifications")
    skill_level = fields.Selection([
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert')
    ], string="Skill Level", default='basic')
    last_evaluation_date = fields.Date(string="Last Evaluation", compute="_compute_last_evaluation")
    # Add this field to properly link equipment to employees
    equipment_ids = fields.One2many('ensa.equipment', 'employee_id', string="Equipment")
    equipment_count = fields.Integer(compute='_compute_equipment_count', string="Equipment Assigned")
    # Add this field to properly link trainings to employees
    training_ids = fields.One2many('ensa.training', 'employee_id', string="Trainings")
    training_count = fields.Integer(compute='_compute_training_count', string="Completed Trainings")
    # Add this field to properly link evaluations to employees
    evaluation_ids = fields.One2many('ensa.evaluation', 'employee_id', string="Evaluations")
    
    # New relationships for smart buttons
    student_project_ids = fields.One2many('ensa.student.project', 'supervisor_id', string="Supervised Projects")
    project_count = fields.Integer(compute='_compute_project_count', string="Projects Count")
    
    internship_ids = fields.One2many('ensa.internship', 'supervisor_id', string="Supervised Internships")
    internship_count = fields.Integer(compute='_compute_internship_count', string="Internships Count")

    # WhatsApp Integration
    whatsapp_number = fields.Char(
        string="WhatsApp Number",
        help="Phone number for WhatsApp notifications (format: +1234567890)"
    )
    whatsapp_verified = fields.Boolean(
        string="WhatsApp Verified",
        default=False,
        help="Whether the WhatsApp number has been verified"
    )
    whatsapp_notifications_enabled = fields.Boolean(
        string="Enable WhatsApp Notifications",
        default=True,
        help="Receive HR notifications via WhatsApp"
    )

    # Performance trend tracking
    avg_performance_score = fields.Float(string="Average Performance Score", compute="_compute_performance_metrics", store=True)
    performance_trend = fields.Selection([
        ('improving', '📈 Improving'),
        ('stable', '→ Stable'),
        ('declining', '📉 Declining'),
        ('no_data', '— No Data')
    ], string="Performance Trend", compute="_compute_performance_metrics", store=True)
    last_3_evaluations = fields.Char(string="Recent Scores", compute="_compute_performance_metrics")
    performance_direction_text = fields.Html(string="Performance Analysis", compute="_compute_performance_metrics")

    # Skill matrix
    technical_skills = fields.Text(string="Technical Skills")
    soft_skills = fields.Text(string="Soft Skills")
    language_skills = fields.Text(string="Languages")

    @api.depends('evaluation_ids.date')  # Correct dependency on our own model
    def _compute_last_evaluation(self):
        for employee in self:
            # Use the related field for better performance
            last_appraisal = employee.evaluation_ids.sorted('date', reverse=True)[:1]
            employee.last_evaluation_date = last_appraisal.date if last_appraisal else False

    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        for employee in self:
            employee.equipment_count = len(employee.equipment_ids)

    @api.depends('training_ids')
    def _compute_training_count(self):
        for employee in self:
            employee.training_count = len(employee.training_ids)

    @api.depends('student_project_ids')
    def _compute_project_count(self):
        for employee in self:
            employee.project_count = len(employee.student_project_ids)

    @api.depends('internship_ids')
    def _compute_internship_count(self):
        for employee in self:
            employee.internship_count = len(employee.internship_ids)

    @api.depends('evaluation_ids.overall_score', 'evaluation_ids.date', 'evaluation_ids.state')
    def _compute_performance_metrics(self):
        """Calculate performance trends and metrics"""
        for employee in self:
            # Get completed evaluations sorted by date (newest first)
            completed_evals = employee.evaluation_ids.filtered(
                lambda e: e.state == 'completed'
            ).sorted('date', reverse=True)
            
            if not completed_evals:
                employee.avg_performance_score = 0.0
                employee.performance_trend = 'no_data'
                employee.last_3_evaluations = "No evaluations yet"
                employee.performance_direction_text = "<p style='color: #999;'>Employee has not been evaluated yet.</p>"
                continue
            
            # Calculate average score
            scores = [e.overall_score for e in completed_evals if e.overall_score > 0]
            employee.avg_performance_score = sum(scores) / len(scores) if scores else 0.0
            
            # Get last 3 evaluations
            recent_evals = completed_evals[:3]
            recent_scores = [str(e.overall_score) for e in recent_evals]
            employee.last_3_evaluations = " → ".join(recent_scores) if recent_scores else "N/A"
            
            # Determine trend
            if len(recent_evals) >= 2:
                # Compare most recent vs previous
                current_score = recent_evals[0].overall_score
                previous_score = recent_evals[1].overall_score
                
                if current_score > previous_score + 0.5:
                    employee.performance_trend = 'improving'
                    trend_html = f"<p style='color: #51a881;'><strong>Performance is Improving</strong><br/>Latest Score: {current_score} (↑ {current_score - previous_score:.1f} points)</p>"
                elif current_score < previous_score - 0.5:
                    employee.performance_trend = 'declining'
                    trend_html = f"<p style='color: #e74c3c;'><strong>Performance is Declining</strong><br/>Latest Score: {current_score} (↓ {previous_score - current_score:.1f} points)</p>"
                else:
                    employee.performance_trend = 'stable'
                    trend_html = f"<p style='color: #5b9fd4;'><strong>Performance is Stable</strong><br/>Latest Score: {current_score} (consistent)</p>"
            else:
                # Single evaluation - can't determine trend
                employee.performance_trend = 'stable'
                current_score = recent_evals[0].overall_score
                trend_html = f"<p style='color: #5b9fd4;'>Latest Score: {current_score}</p>"
            
            # Add recommendation color coding
            if employee.avg_performance_score >= 8.5:
                quality = "<span style='background-color: #51a881; color: white; padding: 3px 8px; border-radius: 3px;'>Excellent</span>"
            elif employee.avg_performance_score >= 7.0:
                quality = "<span style='background-color: #5b9fd4; color: white; padding: 3px 8px; border-radius: 3px;'>Good</span>"
            elif employee.avg_performance_score >= 5.0:
                quality = "<span style='background-color: #f4a460; color: white; padding: 3px 8px; border-radius: 3px;'>Needs Improvement</span>"
            else:
                quality = "<span style='background-color: #e74c3c; color: white; padding: 3px 8px; border-radius: 3px;'>Critical</span>"
            
            employee.performance_direction_text = trend_html + f"<p>Overall Average: {employee.avg_performance_score:.1f}/10 - {quality}</p>"

    @api.constrains('identification_number')
    def _check_identification(self):
        for employee in self:
            if employee.identification_number and len(employee.identification_number) != 8:
                raise ValidationError(_("National ID must be 8 characters long"))

    # Smart buttons
    def action_view_equipment(self):
        return {
            'name': _('Assigned Equipment'),
            'view_mode': 'tree,form',
            'res_model': 'ensa.equipment',
            'domain': [('employee_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_employee_id': self.id}
        }

    def action_view_trainings(self):
        return {
            'name': _('Completed Trainings'),
            'view_mode': 'tree,form',
            'res_model': 'ensa.training',
            'domain': [('employee_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_employee_id': self.id}
        }

    def action_view_evaluations(self):
        return {
            'name': _('Performance Evaluations'),
            'view_mode': 'tree,form',
            'res_model': 'ensa.evaluation',
            'domain': [('employee_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_employee_id': self.id}
        }

    def action_view_projects(self):
        return {
            'name': _('Supervised Projects'),
            'view_mode': 'kanban,tree,form',
            'res_model': 'ensa.student.project',
            'domain': [('supervisor_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_supervisor_id': self.id}
        }

    def action_view_internships(self):
        return {
            'name': _('Supervised Internships'),
            'view_mode': 'kanban,tree,form',
            'res_model': 'ensa.internship',
            'domain': [('supervisor_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_supervisor_id': self.id}
        }
    
    def send_whatsapp_notification(self, message: str, media_url: str = None) -> bool:
        """
        Send WhatsApp notification to employee
        
        Args:
            message: Message text to send
            media_url: Optional URL to media file (PDF, image, etc.)
            
        Returns:
            True if sent successfully, False otherwise
        """
        self.ensure_one()
        
        if not self.whatsapp_number or not self.whatsapp_notifications_enabled:
            return False
        
        if not self.whatsapp_verified:
            return False
        
        try:
            return self.env['ensa.whatsapp.service'].send_message(
                to_number=self.whatsapp_number,
                message=message,
                media_url=media_url
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"WhatsApp send failed for {self.name}: {str(e)}")
            return False

class EmployeeCertification(models.Model):
    _name = 'ensa.employee.certification'
    _description = 'Employee Certifications'

    name = fields.Char(string="Certification Name", required=True)
    issuing_body = fields.Char(string="Issuing Body")
    issue_date = fields.Date(string="Issue Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    verification_notes = fields.Text(string="Verification Notes")
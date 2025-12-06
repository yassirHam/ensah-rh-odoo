from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class EmployeeEvaluation(models.Model):
    _name = 'ensa.evaluation'
    _description = 'Employee Performance Evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char(string="Evaluation Reference", required=True, copy=False, 
                      default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    date = fields.Date(string="Evaluation Date", default=fields.Date.today)
    evaluator_id = fields.Many2one('hr.employee', string="Evaluator", 
                                  default=lambda self: self.env.user.employee_id)
    overall_score = fields.Float(string="Overall Score", compute='_compute_score', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Pending Approval'),
        ('approved', 'Approved'),
        ('reviewed', 'Reviewed'),
        ('completed', 'Completed')
    ], string="Status", default='draft', tracking=True)
    
    # Approval fields for workflow
    approval_manager_id = fields.Many2one('hr.employee', string="Approving Manager", 
                                         tracking=True, help="Manager who approves this evaluation")
    approval_date = fields.Date(string="Approval Date", readonly=True, tracking=True)
    approval_comments = fields.Text(string="Manager Comments")
    
    # Evaluation criteria
    technical_score = fields.Float(string="Technical Skills (1-10)")
    productivity_score = fields.Float(string="Productivity (1-10)")
    teamwork_score = fields.Float(string="Teamwork (1-10)")
    innovation_score = fields.Float(string="Innovation (1-10)")
    attendance_score = fields.Float(string="Attendance (1-10)")

    comments = fields.Text(string="Evaluator Comments")
    improvement_plan = fields.Text(string="Improvement Plan")
    
    # AI-generated insights
    ai_insights = fields.Html(string="AI Performance Insights", readonly=True)
    recommendation = fields.Selection([
        ('promote', 'Recommend for Promotion'),
        ('retain', 'Retain Current Position'),
        ('improve', 'Needs Improvement'),
        ('replace', 'Consider Replacement')
    ], string="AI Recommendation", readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('ensa.evaluation') or _('New')
        return super(EmployeeEvaluation, self).create(vals)

    @api.depends('technical_score', 'productivity_score', 'teamwork_score', 
                 'innovation_score', 'attendance_score')
    def _compute_score(self):
        for rec in self:
            scores = [
                rec.technical_score,
                rec.productivity_score,
                rec.teamwork_score,
                rec.innovation_score,
                rec.attendance_score
            ]
            valid_scores = [s for s in scores if s > 0]
            rec.overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

    def action_submit(self):
        """Submit evaluation for manager approval"""
        if not self.approval_manager_id:
            raise ValidationError(_("Please select an approving manager before submitting."))
        
        self.write({'state': 'submitted'})
        
        # Generate AI insights
        self._generate_ai_insights()
        
        # Create approval task for manager
        self.activity_schedule(
            'mail.mail_activity_data_review',
            summary=f"Evaluation Approval Needed for {self.employee_id.name}",
            note=f"Please review and approve/reject the evaluation.\n\nOverall Score: {self.overall_score}\nRecommendation: {self.recommendation}",
            user_id=self.approval_manager_id.user_id.id
        )
        
        # Send email notification to manager
        template = self.env.ref('ensa_hoceima_hr.email_template_evaluation_submitted', False)
        if template:
            template.send_mail(self.id, force_send=True)
        
        self.message_post(body=_("Evaluation submitted for manager approval"))

    def action_approve(self):
        """Manager approves the evaluation"""
        if not self.env.user.has_group('hr.group_hr_manager'):
            raise UserError(_("Only HR managers can approve evaluations"))
        
        self.write({
            'state': 'approved',
            'approval_date': fields.Date.today()
        })
        
        self.message_post(body=_("Evaluation approved by %s") % self.env.user.name)
        
        # Create activity for final review
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=f"Review Approved Evaluation - {self.employee_id.name}",
            note="Evaluation has been approved and is ready for final review.",
            user_id=self.evaluator_id.user_id.id
        )
        
        # Send approval notification to employee
        template = self.env.ref('ensa_hoceima_hr.email_template_evaluation_approved', False)
        if template:
            template.send_mail(self.id, force_send=True)

    def action_reject(self):
        """Reject evaluation and return to draft"""
        self.write({'state': 'draft'})
        self.message_post(body=_("Evaluation rejected by manager. Please revise and resubmit."))

    def action_review(self):
        """Mark evaluation as reviewed"""
        self.write({'state': 'reviewed'})
        self.message_post(body=_("Evaluation marked as reviewed"))

    def action_complete(self):
        """Complete the evaluation process"""
        if self.state != 'reviewed':
            raise UserError(_("Evaluation must be reviewed before completion"))
        
        self.write({'state': 'completed'})
        
        # Trigger improvement plan notifications
        if self.improvement_plan:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                note=f"Follow up on improvement plan: {self.improvement_plan}",
                user_id=self.employee_id.parent_id.user_id.id or self.env.user.id
            )
        
        self.message_post(body=_("Evaluation process completed. Employee notified."))
        
        # Send notification to employee
        self.employee_id.message_post(
            body=f"Your performance evaluation for {self.date.strftime('%B %Y')} has been completed.<br/>"
                 f"Overall Score: {self.overall_score}<br/>"
                 f"Recommendation: {dict(self._fields['recommendation'].selection).get(self.recommendation)}"
        )

    def action_reset_draft(self):
        """Reset evaluation to draft state"""
        if self.state == 'completed':
            raise UserError(_("Cannot reset a completed evaluation"))
        
        self.write({'state': 'draft'})
        self.message_post(body=_("Evaluation has been reset to draft state"))

    def _generate_ai_insights(self):
        """Simulate AI analysis - in production this would integrate with ML service"""
        for rec in self:
            if rec.overall_score >= 8.5:
                rec.write({
                    'ai_insights': "<p>Exceptional performance across all metrics. Ready for leadership roles.</p>",
                    'recommendation': 'promote'
                })
            elif rec.overall_score >= 7.0:
                rec.write({
                    'ai_insights': "<p>Strong performer with good growth potential. Focus on innovation skills.</p>",
                    'recommendation': 'retain'
                })
            elif rec.overall_score >= 5.0:
                rec.write({
                    'ai_insights': "<p>Meets expectations but needs development in key areas. Implement improvement plan.</p>",
                    'recommendation': 'improve'
                })
            else:
                rec.write({
                    'ai_insights': "<p>Performance below expectations despite support. Consider role adjustment.</p>",
                    'recommendation': 'replace'
                })
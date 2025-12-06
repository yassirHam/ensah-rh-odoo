from odoo import models, fields, api, _

class EmployeeTraining(models.Model):
    _name = 'ensa.training'
    _description = 'Employee Training Programs'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Training Title", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    trainer_id = fields.Many2one('hr.employee', string="Trainer")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date")
    duration = fields.Float(string="Duration (Hours)", compute='_compute_duration')
    category = fields.Selection([
        ('technical', 'Technical'),
        ('soft_skills', 'Soft Skills'),
        ('compliance', 'Compliance'),
        ('management', 'Management')
    ], string="Category", default='technical')
    status = fields.Selection([
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='planned', tracking=True)
    description = fields.Text(string="Description")
    certification = fields.Boolean(string="Provides Certification")
    cost = fields.Monetary(string="Training Cost")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    feedback = fields.Text(string="Participant Feedback")
    
    # Competency mapping
    competency_improvement = fields.Text(string="Competencies Improved")
    post_training_score = fields.Float(string="Post-Training Assessment")

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for training in self:
            if training.start_date and training.end_date:
                delta = training.end_date - training.start_date
                training.duration = delta.days * 8  # Assuming 8-hour days
            else:
                training.duration = 0.0

    def action_start(self):
        """Start training and send notification to employee"""
        self.write({'status': 'in_progress'})
        
        # Create activity reminder
        self.activity_schedule(
            'mail.mail_activity_data_meeting',
            summary="Training Session",
            note=f"Training: {self.name}",
            user_id=self.employee_id.user_id.id
        )
        
        # Send training started email
        template = self.env.ref('ensa_hoceima_hr.email_template_training_started', False)
        if template:
            template.send_mail(self.id, force_send=True)
        
        self.message_post(body=_("Training started. Notification sent to employee."))

    def action_complete(self):
        """Complete training and send notification"""
        self.write({'status': 'completed'})
        
        # Send training completion email
        template = self.env.ref('ensa_hoceima_hr.email_template_training_completed', False)
        if template:
            template.send_mail(self.id, force_send=True)
        
        # Send praise for high achievers
        if self.post_training_score > 8.0:
            self.employee_id.message_post(
                body=f"🎉 Excellent performance in training: {self.name} (Score: {self.post_training_score})"
            )
        
        self.message_post(body=_("Training completed. Completion certificate sent to employee."))

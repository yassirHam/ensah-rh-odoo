from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StudentInternship(models.Model):
    _name = 'ensa.internship'
    _description = 'Student Internships'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Internship Number", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    student_name = fields.Char(string="Student Name", required=True)
    student_email = fields.Char(string="Student Email")
    level = fields.Char(string="Academic Level", help="e.g., 3rd Year, 2nd Year")
    specialization = fields.Char(string="Specialization", help="Engineering specialization")
    host_company = fields.Char(string="Host Company", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    duration = fields.Float(string="Duration (Months)")
    status = fields.Selection([
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended')
    ], string="Status", default='planned', tracking=True)
    supervisor_id = fields.Many2one('hr.employee', string="Supervisor")
    internship_type = fields.Selection([
        ('industrial', 'Industrial'),
        ('research', 'Research'),
        ('academic', 'Academic'),
        ('other', 'Other')
    ], string="Internship Type", default='industrial')
    description = fields.Text(string="Description", help="Project description and responsibilities")
    report_score = fields.Float(string="Report Score", help="Final internship report score")
    learning_outcomes = fields.Text(string="Learning Outcomes")
    
    # Additional tracking
    created_date = fields.Date(string="Created Date", readonly=True, default=fields.Date.context_today)
    modified_date = fields.Date(string="Last Modified", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('ensa.internship') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        vals['modified_date'] = fields.Date.context_today(self)
        return super().write(vals)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for internship in self:
            if internship.end_date < internship.start_date:
                raise ValidationError(_("End date must be after or equal to start date."))

    @api.constrains('report_score')
    def _check_report_score(self):
        for internship in self:
            if internship.report_score and (internship.report_score < 0 or internship.report_score > 20):
                raise ValidationError(_("Report score must be between 0 and 20."))

    def action_start(self):
        self.write({'status': 'in_progress'})
        self.message_post(body=_("Internship started."))

    def action_complete(self):
        self.write({'status': 'completed'})
        self.message_post(body=_("Internship completed successfully."))

    def action_suspend(self):
        self.write({'status': 'suspended'})
        self.message_post(body=_("Internship suspended."))

    def action_cancel(self):
        self.write({'status': 'cancelled'})
        self.message_post(body=_("Internship cancelled."))

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StudentProject(models.Model):
    _name = 'ensa.student.project'
    _description = 'Student Projects'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Project Number", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string="Project Title", required=True)
    description = fields.Text(string="Description")
    supervisor_id = fields.Many2one('hr.employee', string="Supervisor", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    status = fields.Selection([
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='planning', tracking=True)
    domain = fields.Char(string="Domain/Field", help="Engineering domain or specialization")
    budget = fields.Monetary(string="Budget")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    technology_stack = fields.Text(string="Technology Stack", help="Technologies and tools used")
    
    # Project outcomes and deliverables
    deliverables = fields.Text(string="Deliverables")
    outcomes = fields.Text(string="Learning Outcomes")
    final_grade = fields.Float(string="Final Grade")
    
    # Tracking
    created_date = fields.Date(string="Created Date", readonly=True, default=fields.Date.context_today)
    modified_date = fields.Date(string="Last Modified", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('ensa.student.project') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        vals['modified_date'] = fields.Date.context_today(self)
        return super().write(vals)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for project in self:
            if project.end_date < project.start_date:
                raise ValidationError(_("End date must be after or equal to start date."))

    @api.constrains('budget')
    def _check_budget(self):
        for project in self:
            if project.budget and project.budget < 0:
                raise ValidationError(_("Budget cannot be negative."))

    def action_start(self):
        self.write({'status': 'in_progress'})
        self.message_post(body=_("Project started."))

    def action_complete(self):
        self.write({'status': 'completed'})
        self.message_post(body=_("Project completed successfully."))

    def action_hold(self):
        self.write({'status': 'on_hold'})
        self.message_post(body=_("Project put on hold."))

    def action_cancel(self):
        self.write({'status': 'cancelled'})
        self.message_post(body=_("Project cancelled."))

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EmployeeEquipment(models.Model):
    _name = 'ensa.equipment'
    _description = 'Employee Equipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'assignment_date desc'

    name = fields.Char(string="Equipment Name", required=True)
    employee_id = fields.Many2one('hr.employee', string="Assigned To")
    equipment_type = fields.Selection([
        ('computer', 'Computer'),
        ('phone', 'Phone'),
        ('vehicle', 'Vehicle'),
        ('tools', 'Tools'),
        ('other', 'Other')
    ], string="Type", default='computer')
    serial_number = fields.Char(string="Serial Number", copy=False)
    assignment_date = fields.Date(string="Assignment Date")
    return_date = fields.Date(string="Return Date")
    condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], string="Condition at Assignment", default='good')
    return_condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], string="Condition at Return")
    notes = fields.Text(string="Notes")
    state = fields.Selection([
        ('available', 'In Stock'),
        ('assigned', 'Assigned'),
        ('returned', 'Returned'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost')
    ], string="Status", default='available', tracking=True)
    active = fields.Boolean(string="Active", default=True)
    value = fields.Monetary(string="Asset Value")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    warranty_expiry = fields.Date(string="Warranty Expiry")

    def action_assign(self):
        """Quick assignment to an employee"""
        self.ensure_one()
        if not self.employee_id:
             raise ValidationError(_("Please select an employee before assigning."))
        self.write({
            'state': 'assigned',
            'assignment_date': fields.Date.today()
        })

    @api.constrains('serial_number')
    def _check_serial_unique(self):
        for equipment in self:
            if equipment.serial_number:
                existing = self.search([
                    ('serial_number', '=', equipment.serial_number),
                    ('id', '!=', equipment.id)
                ], limit=1)
                if existing:
                    raise ValidationError(_("Serial number must be unique across all equipment"))

    def action_return(self):
        self.write({'state': 'returned', 'return_date': fields.Date.today()})
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary="Equipment Return Verification",
            note=f"Verify condition of returned equipment: {self.name}",
            user_id=self.employee_id.parent_id.user_id.id or self.env.user.id
        )

    def action_report_damaged(self):
        self.write({'state': 'damaged'})
        self.message_post(body=_("Equipment reported as damaged by %s") % self.employee_id.name)

    def action_report_lost(self):
        self.write({'state': 'lost'})
        self.message_post(body=_("Equipment reported as lost by %s") % self.employee_id.name)
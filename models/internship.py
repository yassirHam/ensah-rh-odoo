from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StudentInternship(models.Model):
    _name = 'ensa.internship'
    _description = 'Student Internships'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Internship Number", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    student_name = fields.Char(string="Student Name", required=True)
    student_email = fields.Char(string="Student Email")
    student_phone = fields.Char(string="WhatsApp Number", help="Format: +212612345678")
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
    
    # Smart Matching Fields
    student_skills = fields.Text(string="Student Skills", help="Comma-separated skills (e.g., Python, Machine Learning, Research)")
    student_interests = fields.Text(string="Student Interests", help="Student's areas of interest")
    required_skills = fields.Text(string="Required Skills", help="Skills required for this internship")
    required_level = fields.Char(string="Required Academic Level", help="e.g., 3rd Year, Master's")
    match_score = fields.Float(string="Match Score (%)", readonly=True, help="AI-calculated match score (0-100)")
    success_probability = fields.Float(string="Success Probability", readonly=True, help="Predicted probability of successful completion (0-1)")
    match_recommendation = fields.Char(string="Match Recommendation", readonly=True)
    
    # Progress Tracking via WhatsApp
    checkin_ids = fields.One2many('ensa.internship.checkin', 'internship_id', string="Check-ins")
    next_checkin_date = fields.Date(string="Next Check-in Date", compute='_compute_next_checkin', store=True)
    progress_percentage = fields.Float(string="Progress %", compute='_compute_progress', store=True)
    risk_level = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk')
    ], string="Risk Level", compute='_compute_risk_level', store=True)
    
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
    
    # ============ NEW AI MATCHING METHODS ============
    
    @api.depends('checkin_ids', 'checkin_ids.checkin_date')
    def _compute_next_checkin(self):
        """Calculate next check-in date (weekly)"""
        for internship in self:
            if internship.status == 'in_progress':
                last_checkin = internship.checkin_ids.sorted('checkin_date', reverse=True)[:1]
                if last_checkin:
                    # Next check-in is 7 days after last check-in
                    from datetime import timedelta
                    internship.next_checkin_date = last_checkin.checkin_date + timedelta(days=7)
                else:
                    # First check-in is 7 days after start date
                    from datetime import timedelta
                    internship.next_checkin_date = internship.start_date + timedelta(days=7) if internship.start_date else False
            else:
                internship.next_checkin_date = False
    
    @api.depends('start_date', 'end_date', 'checkin_ids')
    def _compute_progress(self):
        """Calculate progress based on time and check-ins"""
        for internship in self:
            if internship.start_date and internship.end_date:
                total_days = (internship.end_date - internship.start_date).days
                if total_days > 0:
                    elapsed_days = (fields.Date.today() - internship.start_date).days
                    time_progress = min((elapsed_days / total_days) * 100, 100)
                    internship.progress_percentage = max(0, time_progress)
                else:
                    internship.progress_percentage = 0
            else:
                internship.progress_percentage = 0
    
    @api.depends('checkin_ids', 'checkin_ids.sentiment')
    def _compute_risk_level(self):
        """Calculate risk level based on check-ins sentiment"""
        for internship in self:
            checkins = internship.checkin_ids.sorted('checkin_date', reverse=True)[:3]
            if not checkins:
                internship.risk_level = 'low'
                continue
            
            # Count concerning check-ins
            concerning_count = len(checkins.filtered(lambda c: c.sentiment == 'concerning'))
            
            if concerning_count >= 2:
                internship.risk_level = 'high'
            elif concerning_count == 1:
                internship.risk_level = 'medium'
            else:
                internship.risk_level = 'low'
    
    def calculate_match_score(self, student_data=None):
        """
        Calculate match score between student and internship
        Can be called with student_data dict or uses internship's own student data
        """
        self.ensure_one()
        
        # Check if smart matching is enabled
        if self.env['ir.config_parameter'].sudo().get_param('ensa_hr.enable_smart_matching', 'True') != 'True':
            return
        
        try:
            matching_engine = self.env['ensa.matching.engine'].get_matching_engine()
            
            # Prepare student data
            if not student_data:
                student_skills_list = [s.strip() for s in (self.student_skills or '').split(',') if s.strip()]
                student_data = {
                    'skills': student_skills_list,
                    'interests': self.student_interests or '',
                    'avg_score': 7.0,  # Default if not provided
                    'level': self.level or ''
                }
            
            # Prepare internship data
            required_skills_list = [s.strip() for s in (self.required_skills or '').split(',') if s.strip()]
            internship_data = {
                'required_skills': required_skills_list,
                'description': self.description or '',
                'type': self.internship_type or '',
                'required_level': self.required_level or ''
            }
            
            # Calculate match
            match_result = matching_engine.match_student_to_internship(student_data, internship_data)
            
            # Update fields
            self.write({
                'match_score': match_result.get('total_score', 0),
                'match_recommendation': match_result.get('recommendation', ''),
                'success_probability': matching_engine.predict_success_probability(
                    student_data,
                    internship_data,
                    match_result.get('total_score', 0)
                )
            })
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Match calculation failed: {str(e)}")
    
    def send_weekly_checkin_request(self):
        """Send WhatsApp check-in request to student"""
        self.ensure_one()
        
        if not self.student_email or self.status != 'in_progress':
            return
        
        try:
            # Check if WhatsApp bot is enabled
            if self.env['ir.config_parameter'].sudo().get_param('ensa_hr.enable_whatsapp_bot', 'True') != 'True':
                return
            
            whatsapp_service = self.env['ensa.whatsapp.service'].get_whatsapp_service()
            
            # Prepare notification data
            data = {
                'student_name': self.student_name,
                'company_name': self.host_company
            }
            
            # Send notification (need student phone number - will add to model later)
            # For now, log the action
            self.message_post(body=_("Weekly check-in request scheduled to be sent via WhatsApp"))
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"WhatsApp check-in request failed: {str(e)}")
    
    def analyze_progress_with_ai(self):
        """Use AI to analyze progress and detect issues"""
        self.ensure_one()
        
        try:
            if self.env['ir.config_parameter'].sudo().get_param('ensa_hr.enable_ai_features', 'True') != 'True':
                return
            
            ai_service = self.env['ensa.ai.service'].get_ai_service()
            
            # Gather check-in data
            checkin_texts = [c.message for c in self.checkin_ids.sorted('checkin_date', reverse=True)[:5]]
            
            prompt = f"""Analyze these internship progress check-ins and identify any red flags:

Internship: {self.name} at {self.host_company}
Student: {self.student_name}
Progress: {self.progress_percentage}%
Recent check-ins:
{chr(10).join(['- ' + txt for txt in checkin_texts if txt])}

Detect:
1. Any struggling or difficulty mentions
2. Lack of learning/progress
3. Communication issues
4. Technical challenges

Return JSON: {{"has_issues": true/false, "severity": "low/medium/high", "summary": "...", "recommended_action": "..."}}"""
            
            response = ai_service.generate_text(prompt, max_tokens=300, temperature=0.3)
            
            # Parse and act on results
            import json
            try:
                analysis = json.loads(response)
                if analysis.get('has_issues') and analysis.get('severity') in ['medium', 'high']:
                    # Notify supervisor
                    if self.supervisor_id and self.supervisor_id.user_id:
                        self.activity_schedule(
                            'mail.mail_activity_data_warning',
                            summary=f"Internship Issue Detected - {self.student_name}",
                            note=f"AI detected potential issues:\n\n{analysis.get('summary')}\n\nRecommended: {analysis.get('recommended_action')}",
                            user_id=self.supervisor_id.user_id.id
                        )
            except json.JSONDecodeError:
                pass
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"AI progress analysis failed: {str(e)}")

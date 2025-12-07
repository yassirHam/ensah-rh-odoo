from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.fields import Date
from datetime import timedelta

class TestStudentProject(TransactionCase):

    def setUp(self):
        super(TestStudentProject, self).setUp()
        self.supervisor = self.env['hr.employee'].create({'name': 'Dr. Supervisor'})
        self.project_vals = {
            'title': 'Test Project',
            'supervisor_id': self.supervisor.id,
            'start_date': Date.today(),
            'end_date': Date.today() + timedelta(days=90),
            'budget': 1000.0,
        }

    def test_project_lifecycle(self):
        """Test the lifecycle of a student project"""
        project = self.env['ensa.student.project'].create(self.project_vals)
        self.assertEqual(project.status, 'planning')
        
        project.action_start()
        self.assertEqual(project.status, 'in_progress')
        
        project.action_complete()
        self.assertEqual(project.status, 'completed')

    def test_date_constraints(self):
        """Test that end date cannot be before start date"""
        with self.assertRaises(ValidationError):
            self.env['ensa.student.project'].create({
                'title': 'Invalid Date Project',
                'supervisor_id': self.supervisor.id,
                'start_date': Date.today(),
                'end_date': Date.today() - timedelta(days=1),
            })

    def test_budget_constraints(self):
        """Test that budget cannot be negative"""
        with self.assertRaises(ValidationError):
            self.env['ensa.student.project'].create({
                'title': 'Negative Budget Project',
                'supervisor_id': self.supervisor.id,
                'start_date': Date.today(),
                'end_date': Date.today() + timedelta(days=30),
                'budget': -100.0,
            })

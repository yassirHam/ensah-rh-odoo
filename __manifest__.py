{
    'name': "Ensa Hoceima HR",
    'summary': "Advanced HR Management System with Modern Dashboard",
    'description': """
        Enterprise-grade HR solution featuring:
        - Smart employee profiles with skill matrices
        - AI-powered performance evaluations
        - Equipment lifecycle management
        - Interactive real-time dashboard
        - Advanced reporting engine
    """,
    'author': "Ensa Hoceima",
    'category': 'Human Resources',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'hr_contract',
        'hr_attendance',
        'hr_holidays',
        'hr_recruitment',
        'web'  # CORRECTED: Changed from 'web_dashboard' to 'web'
    ],
    'data': [
    'security/security.xml',
    'security/ir.model.access.csv',
    'data/data.xml',
    # 'data/email_templates.xml',  # TEMPORARILY DISABLED: XML schema validation issue
    'views/evaluation_views.xml',
    'views/training_views.xml',
    'views/equipment_views.xml',
    'views/employee_views.xml',         # Must come before menu (menu references action_ensa_employee_analysis)
    'views/student_project_views.xml',  # NEW: Student projects UI
    'views/internship_views.xml',       # NEW: Internships UI
    'views/certification_views.xml',    # NEW: Certification UI (Must be before analytics)
    'views/analytics_views.xml',        # NEW: Department analytics dashboards
    'views/dashboard_views.xml',
    'views/menu.xml',                   # Must come after all view files
    'report/report_templates.xml',
    'report/employee_report.xml',
    ],
    'assets': {
        'web.assets_common': [
            'ensa_hoceima_hr/static/src/scss/dashboard.scss',
            'ensa_hoceima_hr/static/src/scss/employee.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
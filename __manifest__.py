{
    'name': "Ensa Hoceima HR",
    'summary': "Advanced HR Management System with Modern Dashboard",
    'description': """
        Enterprise-grade HR solution featuring:
        - AI Chat Assistant for natural language HR queries
        - Smart Dashboard with real-time AI insights
        - AI-powered performance evaluations with recommendations
        - Turnover risk predictions and anomaly detection
        - Predictive analytics and data visualization suggestions
        - Equipment lifecycle management
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
        'web'
    ],
    'external_dependencies': {
        'python': ['qrcode'],
    },
    'images': ['static/description/t1.png'],
    'web_icon': 'ensa_hoceima_hr,static/description/icon.png',
    'data': [
    'security/security.xml',
    'security/ir.model.access.csv',
    'data/data.xml',
    'views/base_menu.xml',              # Must be first (defines root menu)
    # 'data/email_templates.xml',  # TEMPORARILY DISABLED: XML schema validation issue
    'views/evaluation_views.xml',
    'views/training_views.xml',
    'views/equipment_views.xml',
    'views/employee_views.xml',         # Must come before menu (menu references action_ensa_employee_analysis)
    'views/student_project_views.xml',  # NEW: Student projects UI
    'views/internship_views.xml',       # NEW: Internships UI
    'views/certification_views.xml',    # NEW: Certification UI (Must be before analytics)
    'views/analytics_views.xml',        # NEW: Department analytics dashboards
    'views/dashboard_views.xml',        # NEW: AI-powered dashboard
    'views/ai_assistant_views.xml',     # NEW: AI chat assistant
    'views/settings_views.xml',         # NEW: AI & WhatsApp configuration
    'views/menu.xml',                   # Must come after all view files
    'report/ensah_report_base.xml',     # Base templates
    'report/report_templates.xml',      # Legacy/Detailed templates
    'report/professional_reports.xml',  # New Professional templates
    'report/report_actions.xml',        # All Report Actions
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
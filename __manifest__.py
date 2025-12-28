{
    'name': "Ensa Hoceima HR",
    'summary': "ENSAH HR Management System",
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
    'views/base_menu.xml',              
    'views/evaluation_views.xml',
    'views/training_views.xml',
    'views/equipment_views.xml',
    'views/employee_views.xml',         
    'views/student_project_views.xml',  
    'views/internship_views.xml',       
    'views/certification_views.xml',    
    'views/analytics_views.xml',        
    'views/dashboard_views.xml',        
    'views/ai_assistant_views.xml',     
    'views/settings_views.xml',         
    'views/menu.xml',                   
    'report/ensah_report_base.xml',     
    'report/report_templates.xml',      
    'report/professional_reports.xml',  
    'report/report_actions.xml',        
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
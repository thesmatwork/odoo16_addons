{
    'name': 'Generic Task & Message System',
    'version': '16.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Generic task and messaging system for any business use case',
    'description': """
        Flexible task and messaging module that can be used for:
        - Sales todos and follow-ups
        - Project management tasks
        - HR reminders and assignments
        - Customer service tickets
        - Any custom workflow requirements
    """,
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/task_categories.xml',
        'views/generic_task_views.xml',
        'views/generic_message_views.xml',
        'views/task_category_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
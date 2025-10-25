{
    'name': 'Sales Todo & Messaging',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': 'Todo and messaging system for sales team',
    'description': """
Sales Todo & Messaging System
-----------------------------
Features:
- Personal and assigned todos
- Management messaging system
- Priority management
- Real-time updates support
    """,
    'depends': ['base', 'sale', 'crm'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sales_todo_views.xml',
        'views/sales_message_views.xml',
        'data/data.xml',
    ],
    'installable': True,
    'application': True,
}

{
    'name': 'Contacts Tagline',
    'version': '16.0.1.0.0',
    'category': 'Contacts',
    'summary': 'Add a tagline field to contacts',
    'description': 'This module adds a tagline field to contacts (res.partner).',
    'author': 'Nithya',
    'depends': ['contacts'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
}
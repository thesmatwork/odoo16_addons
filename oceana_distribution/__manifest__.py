{
    'name': 'Oceana Distribution Management',
    'version': '16.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Distributor Purchase Orders and Stock Management',
    'description': """
Oceana Distribution Management System
====================================

* Distributor purchase orders for empty bottles
* Stock management per distributor  
* Low stock alerts
* Integration with sales orders
    """,
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'depends': [
        'base',
        'sale',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/distributor_purchase_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 10,
}

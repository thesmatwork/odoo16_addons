{
    'name': 'Purchase Manual Shipment Adjustment',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Track manual shipped quantities for distributor purchase orders',
    'description': """
        Adds manual shipment tracking fields to distributor purchase order lines.
        
        Features:
        - Track actual shipped quantity vs ordered quantity
        - Calculate variance automatically
        - Store adjustment notes and reasons
        - Track who made adjustments and when
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['oceana_distribution'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

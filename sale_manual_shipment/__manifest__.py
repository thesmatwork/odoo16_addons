{
    'name': 'Sales Manual Shipment Adjustment',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': 'Track manual shipped quantities - API optimized',
    'description': """
        Adds manual shipment tracking fields to sales order lines.
        Optimized for external API consumption via FastAPI.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['sale_management', 'stock', 'base'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

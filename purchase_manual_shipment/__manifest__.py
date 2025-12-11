{
    'name': 'Purchase Manual Shipment Adjustment',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Track manual shipped quantities for distributor purchase orders - API optimized',
    'description': """
        Adds manual shipment tracking fields to distributor purchase order lines.
        Optimized for external API consumption via FastAPI.
        
        Features:
        - Track actual shipped quantity vs ordered quantity
        - Calculate variance automatically
        - Store adjustment notes and reasons
        - Track who made adjustments and when
        - API-friendly methods for reporting
        
        Mirrors the sale_manual_shipment functionality for purchase orders.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base'],  # Assumes distributor.purchase.order.line already exists
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

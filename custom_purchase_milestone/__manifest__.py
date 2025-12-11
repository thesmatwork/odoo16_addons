{
    'name': 'Distributor Purchase Order Milestone',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Track delivery milestones for distributor purchase orders',
    'description': """
        Adds delivery milestone tracking to distributor purchase orders.
        Mirrors the custom_sale_milestone functionality for purchase orders.
        
        Milestones:
        - draft: Order created
        - payment_pending: Awaiting payment confirmation
        - confirmed: Payment confirmed
        - shipped: Order shipped
        - delivered: Order delivered
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base'],  # Assumes distributor.purchase.order already exists
    'data': [
        'views/distributor_purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

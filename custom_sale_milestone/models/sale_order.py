from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    x_delivery_milestone = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Payment Confirmed'),
        ('partial_shipped', 'Partially Shipped'),
        ('shipped', 'Shipped'),
        ('excess_shipped', 'Excess Shipped'),
        ('delivered', 'Delivered'),
        ('done', 'Done'),
    ], string='Delivery Milestone', default='draft', tracking=True)

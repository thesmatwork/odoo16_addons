from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    x_delivery_milestone = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Payment Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ], string='Delivery Milestone', default='draft', tracking=True)

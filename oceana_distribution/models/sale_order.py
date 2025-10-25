from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    distributor_id = fields.Many2one(
        'res.partner',
        string='Distributor',
        domain=[('is_distributor', '=', True)],
        help='The distributor whose inventory is being sold'
    )

from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_distributor = fields.Boolean(
        string='Is Distributor',
        help='Check this box if this partner is a distributor'
    )
    
    distributor_purchase_order_ids = fields.One2many(
        'distributor.purchase.order',
        'distributor_id',
        string='Purchase Orders'
    )
    
    distributor_purchase_count = fields.Integer(
        string='Purchase Orders Count',
        compute='_compute_distributor_purchase_count'
    )
    
    def _compute_distributor_purchase_count(self):
        for partner in self:
            partner.distributor_purchase_count = len(partner.distributor_purchase_order_ids)
    
    def action_view_distributor_purchases(self):
        """Smart button action to view distributor purchase orders"""
        action = self.env.ref('oceana_distribution.action_distributor_purchase_order').read()[0]
        action['domain'] = [('distributor_id', '=', self.id)]
        action['context'] = {'default_distributor_id': self.id}
        return action
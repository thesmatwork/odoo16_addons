from odoo import models, fields, api


class DistributorPurchaseOrder(models.Model):
    _inherit = 'distributor.purchase.order'

    x_delivery_milestone = fields.Selection([
        ('draft', 'Draft'),
        ('payment_pending', 'Payment Pending'),
        ('confirmed', 'Payment Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ], string='Delivery Milestone', default='draft', tracking=True,
       help='Track the delivery progress of this purchase order')

    # Optional: Track estimated delivery date
    x_estimated_delivery = fields.Date(
        string='Estimated Delivery',
        help='Expected delivery date for this order'
    )

    x_delivery_notes = fields.Text(
        string='Delivery Notes',
        help='Additional notes about delivery'
    )

    @api.model
    def create(self, vals):
        """Ensure new orders start with draft milestone"""
        if 'x_delivery_milestone' not in vals:
            vals['x_delivery_milestone'] = 'draft'
        return super(DistributorPurchaseOrder, self).create(vals)

    def action_set_payment_pending(self):
        """Set milestone to payment pending"""
        self.write({'x_delivery_milestone': 'payment_pending'})

    def action_confirm_payment(self):
        """Set milestone to confirmed (payment received)"""
        self.write({'x_delivery_milestone': 'confirmed'})

    def action_mark_shipped(self):
        """Set milestone to shipped"""
        self.write({'x_delivery_milestone': 'shipped'})

    def action_mark_delivered(self):
        """Set milestone to delivered"""
        self.write({'x_delivery_milestone': 'delivered'})

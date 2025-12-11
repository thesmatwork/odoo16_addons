from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DistributorPurchaseOrderLine(models.Model):
    _inherit = 'distributor.purchase.order.line'

    manual_shipped_qty = fields.Float(
        string='Manual Shipped Qty',
        digits='Product Unit of Measure',
        help='Actual quantity shipped (use when it differs from ordered quantity)',
        copy=False,
        index=True,
    )

    qty_diff_manual = fields.Float(
        string='Shipment Variance',
        compute='_compute_qty_diff_manual',
        store=True,
        digits='Product Unit of Measure',
        help='Difference between ordered and manually shipped quantity',
        index=True,
    )

    adjustment_note = fields.Char(
        string='Adjustment Reason',
        help='Reason for shipment quantity difference',
        copy=False,
    )

    manual_adjusted = fields.Boolean(
        string='Manually Adjusted',
        compute='_compute_manual_adjusted',
        store=True,
        help='Line has manual shipment adjustment',
        index=True,
    )

    adjustment_date = fields.Datetime(
        string='Adjustment Date',
        help='When manual quantity was last modified',
        copy=False,
        readonly=True,
    )

    adjustment_user_id = fields.Many2one(
        'res.users',
        string='Adjusted By',
        help='User who made the manual adjustment',
        copy=False,
        readonly=True,
    )

    line_shipment_status = fields.Selection([
        ('pending', 'Pending'),
        ('partial', 'Partially Shipped'),
        ('shipped', 'Fully Shipped'),
    ], string='Line Status', compute='_compute_line_shipment_status', store=True)

    @api.depends('quantity', 'manual_shipped_qty')
    def _compute_qty_diff_manual(self):
        for line in self:
            if line.manual_shipped_qty and line.manual_shipped_qty > 0:
                line.qty_diff_manual = line.quantity - line.manual_shipped_qty
            else:
                line.qty_diff_manual = 0.0

    @api.depends('manual_shipped_qty', 'quantity')
    def _compute_manual_adjusted(self):
        for line in self:
            line.manual_adjusted = (
                bool(line.manual_shipped_qty) and
                line.manual_shipped_qty != line.quantity
            )

    @api.depends('quantity', 'manual_shipped_qty')
    def _compute_line_shipment_status(self):
        for line in self:
            if not line.manual_shipped_qty or line.manual_shipped_qty == 0:
                line.line_shipment_status = 'pending'
            elif line.manual_shipped_qty >= line.quantity:
                line.line_shipment_status = 'shipped'
            else:
                line.line_shipment_status = 'partial'

    def write(self, vals):
        """Track when manual_shipped_qty is modified"""
        if 'manual_shipped_qty' in vals:
            vals = dict(vals)
            vals['adjustment_date'] = fields.Datetime.now()
            vals['adjustment_user_id'] = self.env.user.id
        return super(DistributorPurchaseOrderLine, self).write(vals)

    @api.constrains('manual_shipped_qty')
    def _check_manual_shipped_qty(self):
        for line in self:
            if line.manual_shipped_qty < 0:
                raise ValidationError(
                    "Manual shipped quantity cannot be negative for product '{}'.".format(
                        line.product_id.name or ''
                    )
                )

    def get_manual_shipment_data(self):
        """
        Helper method for API: Returns JSON-friendly dict with all relevant data.
        """
        self.ensure_one()
        order = self.order_id
        distributor = order.distributor_id if order else None
        return {
            'id': self.id,
            'order_id': order.id if order else None,
            'order_name': order.name if order else None,
            'order_date': order.order_date.isoformat() if order and order.order_date else None,
            'distributor_id': distributor.id if distributor else None,
            'distributor_name': distributor.name if distributor else None,
            'product_id': self.product_id.id if self.product_id else None,
            'product_name': self.product_id.name if self.product_id else None,
            'product_code': self.product_id.default_code if self.product_id else None,
            'ordered_qty': float(self.quantity or 0.0),
            'manual_shipped_qty': float(self.manual_shipped_qty or 0.0),
            'variance': float(self.qty_diff_manual or 0.0),
            'adjustment_note': self.adjustment_note or '',
            'manually_adjusted': bool(self.manual_adjusted),
            'line_shipment_status': self.line_shipment_status or 'pending',
            'adjustment_date': self.adjustment_date.isoformat() if self.adjustment_date else None,
            'adjusted_by': self.adjustment_user_id.name if self.adjustment_user_id else None,
            'adjusted_by_id': self.adjustment_user_id.id if self.adjustment_user_id else None,
            'unit_price': float(self.unit_price or 0.0),
            'subtotal': float(self.subtotal or 0.0),
        }

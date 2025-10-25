from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    manual_shipped_qty = fields.Float(
        string='Manual Shipped Qty',
        digits='Product Unit of Measure',
        help='Actual quantity shipped (use when it differs from delivery order)',
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

    @api.depends('product_uom_qty', 'manual_shipped_qty')
    def _compute_qty_diff_manual(self):
        for line in self:
            if line.manual_shipped_qty and line.manual_shipped_qty > 0:
                line.qty_diff_manual = line.product_uom_qty - line.manual_shipped_qty
            else:
                line.qty_diff_manual = 0.0

    @api.depends('manual_shipped_qty', 'product_uom_qty')
    def _compute_manual_adjusted(self):
        for line in self:
            line.manual_adjusted = (
                bool(line.manual_shipped_qty) and
                line.manual_shipped_qty != line.product_uom_qty
            )

    def write(self, vals):
        """Track when manual_shipped_qty is modified"""
        if 'manual_shipped_qty' in vals:
            vals = dict(vals)  # copy to avoid mutating incoming dict
            vals['adjustment_date'] = fields.Datetime.now()
            vals['adjustment_user_id'] = self.env.user.id
        return super(SaleOrderLine, self).write(vals)

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
        Can be called directly from FastAPI endpoint via odoorpc or xmlrpc.
        """
        self.ensure_one()
        order = self.order_id
        partner = self.order_partner_id or order.partner_id
        return {
            'id': self.id,
            'order_id': order.id if order else None,
            'order_name': order.name if order else None,
            'order_date': order.date_order.isoformat() if order and order.date_order else None,
            'customer_id': partner.id if partner else None,
            'customer_name': partner.name if partner else None,
            'product_id': self.product_id.id if self.product_id else None,
            'product_name': self.product_id.name if self.product_id else None,
            'product_code': self.product_id.default_code if self.product_id else None,
            'ordered_qty': float(self.product_uom_qty or 0.0),
            'delivered_qty': float(self.qty_delivered or 0.0),
            'manual_shipped_qty': float(self.manual_shipped_qty or 0.0),
            'variance': float(self.qty_diff_manual or 0.0),
            'adjustment_note': self.adjustment_note or '',
            'manually_adjusted': bool(self.manual_adjusted),
            'adjustment_date': self.adjustment_date.isoformat() if self.adjustment_date else None,
            'adjusted_by': self.adjustment_user_id.name if self.adjustment_user_id else None,
            'adjusted_by_id': self.adjustment_user_id.id if self.adjustment_user_id else None,
            'uom': self.product_uom.name if self.product_uom else None,
            'state': self.state,
            'order_state': order.state if order else None,
        }

    @api.model
    def get_variance_report_data(self, filters=None):
        """
        Optimized method for FastAPI: Get all variance data with optional filters.
        filters: dict with keys: date_from (str), date_to (str), customer_ids (list), product_ids (list),
                               has_variance (bool), manual_adjusted_only (bool)
        """
        domain = [('manual_shipped_qty', '>', 0)]

        if filters:
            if filters.get('date_from'):
                domain.append(('order_id.date_order', '>=', filters['date_from']))
            if filters.get('date_to'):
                domain.append(('order_id.date_order', '<=', filters['date_to']))
            if filters.get('customer_ids'):
                domain.append(('order_partner_id', 'in', filters['customer_ids']))
            if filters.get('product_ids'):
                domain.append(('product_id', 'in', filters['product_ids']))
            if filters.get('has_variance'):
                domain.append(('qty_diff_manual', '!=', 0))
            if filters.get('manual_adjusted_only'):
                domain.append(('manual_adjusted', '=', True))

        lines = self.search(domain, order='order_id desc, id desc')
        return [line.get_manual_shipment_data() for line in lines]

    @api.model
    def get_variance_summary(self, group_by='product'):
        """
        Get aggregated variance data for reporting.
        group_by: 'product' | 'customer' | 'order'
        Returns: list of dicts
        """
        if group_by not in ('product', 'customer', 'order'):
            group_by = 'product'

        query = """
            SELECT 
                CASE 
                    WHEN %s = 'product' THEN CAST(sol.product_id AS TEXT)
                    WHEN %s = 'customer' THEN CAST(so.partner_id AS TEXT)
                    ELSE CAST(sol.order_id AS TEXT)
                END as group_key,
                CASE 
                    WHEN %s = 'product' THEN pt.name
                    WHEN %s = 'customer' THEN rp.name
                    ELSE so.name
                END as group_name,
                COUNT(sol.id) as line_count,
                COALESCE(SUM(sol.product_uom_qty),0) as total_ordered,
                COALESCE(SUM(sol.qty_delivered),0) as total_delivered,
                COALESCE(SUM(sol.manual_shipped_qty),0) as total_manual_shipped,
                COALESCE(SUM(sol.qty_diff_manual),0) as total_variance,
                COUNT(CASE WHEN sol.manual_adjusted THEN 1 END) as adjusted_count
            FROM sale_order_line sol
            JOIN sale_order so ON sol.order_id = so.id
            LEFT JOIN product_product pp ON sol.product_id = pp.id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN res_partner rp ON so.partner_id = rp.id
            WHERE sol.manual_shipped_qty > 0
            GROUP BY group_key, group_name
            ORDER BY total_variance DESC
        """
        # pass the same parameter multiple times for the CASE checks
        params = (group_by, group_by, group_by, group_by)
        self.env.cr.execute(query, params)
        results = self.env.cr.dictfetchall()
        return results

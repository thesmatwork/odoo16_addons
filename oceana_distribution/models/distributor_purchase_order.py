from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class DistributorPurchaseOrder(models.Model):
    _name = 'distributor.purchase.order'
    _description = 'Distributor Purchase Order for Empty Bottles'
    _order = 'name desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Order Reference', 
        required=True, 
        copy=False, 
        readonly=True, 
        default=lambda self: self.env['ir.sequence'].next_by_code('distributor.purchase.order') or 'New'
    )
    
    distributor_id = fields.Many2one(
        'res.partner', 
        string='Distributor', 
        required=True,
        domain=[('is_distributor', '=', True)]
    )
    
    order_date = fields.Datetime(
        string='Order Date', 
        default=fields.Datetime.now,
        required=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    # =====================================================
    # DELIVERY MILESTONE TRACKING (from custom_purchase_milestone)
    # =====================================================
    x_delivery_milestone = fields.Selection([
        ('draft', 'Draft'),
        ('payment_pending', 'Payment Pending'),
        ('confirmed', 'Payment Confirmed'),
        ('partial_shipped', 'Partially Shipped'),
        ('shipped', 'Shipped'),
        ('excess_shipped', 'Excess Shipped'),
        ('delivered', 'Delivered'),
    ], string='Delivery Milestone', default='draft', tracking=True,
       help='Track the delivery progress of this purchase order')
    
    order_line_ids = fields.One2many(
        'distributor.purchase.order.line', 
        'order_id', 
        string='Order Lines'
    )
    
    total_amount = fields.Float(
        string='Total Amount', 
        compute='_compute_total_amount',
        store=True
    )
    
    notes = fields.Text(string='Notes')
    
    @api.depends('order_line_ids.subtotal')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(line.subtotal for line in order.order_line_ids)

    @api.model
    def create(self, vals):
        """Ensure new orders start with draft milestone"""
        if 'x_delivery_milestone' not in vals:
            vals['x_delivery_milestone'] = 'draft'
        return super(DistributorPurchaseOrder, self).create(vals)

    # =====================================================
    # MILESTONE ACTION METHODS
    # =====================================================
    def action_set_payment_pending(self):
        """Set milestone to payment pending"""
        self.write({'x_delivery_milestone': 'payment_pending'})

    def action_confirm_payment(self):
        """Set milestone to confirmed (payment received)"""
        self.write({'x_delivery_milestone': 'confirmed'})

    def action_mark_partial_shipped(self):
        """Set milestone to partially shipped"""
        self.write({'x_delivery_milestone': 'partial_shipped'})

    def action_mark_shipped(self):
        """Set milestone to shipped"""
        self.write({'x_delivery_milestone': 'shipped'})

    def action_mark_excess_shipped(self):
        """Set milestone to excess shipped"""
        self.write({'x_delivery_milestone': 'excess_shipped'})

    def action_mark_delivered(self):
        """Set milestone to delivered"""
        self.write({'x_delivery_milestone': 'delivered'})

    # =====================================================
    # EXISTING METHODS
    # =====================================================
    def action_confirm(self):
        import logging
        _logger = logging.getLogger(__name__)
    
        _logger.info("========== CONFIRMING PURCHASE ORDER ==========")
        for order in self:
            _logger.info(f"Order: {order.name}, Distributor: {order.distributor_id.name}")
            if not order.order_line_ids:
                raise UserError("Cannot confirm order without order lines.")
        
            order.state = 'confirmed'
            _logger.info("Creating stock moves...")
            order._create_stock_moves()
            _logger.info("Stock moves created successfully")
    
        return True


    def _delete_action_confirm(self):
        """Confirm the purchase order and create stock moves"""
        for order in self:
            if not order.order_line_ids:
                raise UserError("Cannot confirm order without order lines.")
            
            order.state = 'confirmed'
            order._create_stock_moves()
        return True

    def action_cancel(self):
        """Cancel the purchase order"""
        self.state = 'cancelled'
        return True

    def action_set_to_draft(self):
        """Reset to draft state"""
        self.state = 'draft'
        return True
    
    def _create_stock_moves(self):
        """Create stock moves to distributor location"""
        import logging
        _logger = logging.getLogger(__name__)
        
        for order in self:
            _logger.info(f"Getting/creating location for distributor: {order.distributor_id.name}")
            
            # Find or create distributor location
            distributor_location = order._get_or_create_distributor_location()
            _logger.info(f"Location found/created: ID={distributor_location.id}, Name={distributor_location.name}")
            
            # Create a picking for this order
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'internal'),
                ('warehouse_id.company_id', '=', self.env.company.id)
            ], limit=1)
            
            if not picking_type:
                picking_type = self.env['stock.picking.type'].search([
                    ('code', '=', 'internal')
                ], limit=1)
            
            picking_vals = {
                'picking_type_id': picking_type.id,
                'location_id': self.env.ref('stock.stock_location_stock').id,
                'location_dest_id': distributor_location.id,
                'origin': order.name,
                'move_type': 'direct',
            }
            
            picking = self.env['stock.picking'].create(picking_vals)
            _logger.info(f"Created picking: {picking.name}")
            
            for line in order.order_line_ids:
                if line.quantity > 0:
                    _logger.info(f"Creating move for product {line.product_id.name}, qty: {line.quantity}")
                    
                    # Get the carton UoM (assuming it's stored on the line or use a fixed one)
                    carton_uom = self.env['uom.uom'].search([('name', '=', 'Carton'),('category_id.name', '=', 'Unit')], limit=1)
                    product_base_uom = line.product_id.uom_id
                    
                    # Convert from cartons to product's base UoM
                    quantity_in_base_uom = carton_uom._compute_quantity(
                        line.quantity,  # 5 cartons
                        product_base_uom,  # Convert to base UoM (units)
                        rounding_method='HALF-UP'
                    )
                    
                    _logger.info(f"UoM conversion: {line.quantity} {carton_uom.name} = {quantity_in_base_uom} {product_base_uom.name}")
                    _logger.info(f"Carton UoM factor: {carton_uom.factor}, ratio: {carton_uom.factor_inv}")
                    
                    # Create stock move in base UoM
                    move_vals = {
                        'name': f'Distributor Purchase: {line.product_id.display_name}',
                        'product_id': line.product_id.id,
                        'product_uom_qty': quantity_in_base_uom,
                        'product_uom': product_base_uom.id,
                        'location_id': self.env.ref('stock.stock_location_stock').id,
                        'location_dest_id': distributor_location.id,
                        'picking_id': picking.id,
                        'origin': order.name,
                        'company_id': self.env.company.id,
                    }
                    
                    _logger.info(f"Move values: From location {move_vals['location_id']} to {move_vals['location_dest_id']}")
                    
                    move = self.env['stock.move'].create(move_vals)
                    _logger.info(f"Stock move {move.id} created with qty {quantity_in_base_uom}")
            
            # Confirm the picking
            picking.action_confirm()
            _logger.info(f"Picking confirmed: {picking.name}")
            
            # Check availability
            picking.action_assign()
            _logger.info(f"Picking assigned: {picking.name}, State: {picking.state}")
            
            # Set quantity_done for each move
            for move in picking.move_ids:
                if move.product_uom_qty > 0:
                    move.quantity_done = move.product_uom_qty
                    _logger.info(f"Set quantity_done for {move.product_id.name}: {move.quantity_done}")
            
            # Validate the picking
            try:
                result = picking.with_context(skip_backorder=True).button_validate()
                _logger.info(f"Picking validated: {picking.name}, State: {picking.state}")
                
                # Handle any wizard that appears
                if isinstance(result, dict):
                    if result.get('res_model') == 'stock.backorder.confirmation':
                        backorder_wizard = self.env['stock.backorder.confirmation'].browse(result['res_id'])
                        backorder_wizard.process_cancel_backorder()
                        _logger.info(f"Backorder wizard processed")
                    elif result.get('res_model') == 'stock.immediate.transfer':
                        immediate_transfer = self.env['stock.immediate.transfer'].browse(result['res_id'])
                        immediate_transfer.process()
                        _logger.info(f"Immediate transfer processed")
                    
            except Exception as e:
                _logger.error(f"Error validating picking: {str(e)}")
                raise
            
            # Log final quantities
            for line in order.order_line_ids:
                qty_available = line.product_id.with_context(location=distributor_location.id).qty_available
                _logger.info(f"Available quantity for {line.product_id.name} at {distributor_location.name}: {qty_available}")

    def _qqqcreate_stock_moves(self):
        """Create stock moves to distributor location"""
        for order in self:
            # Find or create distributor location
            distributor_location = order._get_or_create_distributor_location()
            
            for line in order.order_line_ids:
                if line.quantity > 0:
                    # Create stock move
                    move_vals = {
                        'name': f'Distributor Purchase: {line.product_id.display_name}',
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.quantity,
                        'product_uom': line.product_id.uom_id.id,
                        'location_id': self.env.ref('stock.stock_location_stock').id,
                        'location_dest_id': distributor_location.id,
                        'state': 'done',
                        'origin': order.name,
                    }
                    
                    move = self.env['stock.move'].create(move_vals)
                    move._action_done()
    
            
    def _get_or_create_distributor_location(self):
        """Get or create stock location for distributor"""
        import logging
        _logger = logging.getLogger(__name__)
    
        location_name = f'{self.distributor_id.name} Warehouse'
        _logger.info(f"Searching for location with name: {location_name}")
    
        location = self.env['stock.location'].search([
            ('name', '=', location_name),
            ('usage', '=', 'internal')
        ], limit=1)
    
        if not location:
            _logger.info(f"Location not found, creating new one: {location_name}")
        
            # Create new location for distributor
            location = self.env['stock.location'].create({
                'name': location_name,
                'location_id': self.env.ref('stock.stock_location_locations').id,
                'usage': 'internal',
            })
        
            _logger.info(f"Location created: ID={location.id}, Name={location.name}")
        else:
            _logger.info(f"Location found: ID={location.id}, Name={location.name}")
    
        return location
        

    def _qqqget_or_create_distributor_location(self):
        """Get or create stock location for distributor"""
        # Search by name instead of partner_id
        location_name = f'{self.distributor_id.name} Warehouse'
        print("-----------------------------------" + str(location_name))  
        location = self.env['stock.location'].search([
            ('name', '=', location_name),
            ('usage', '=', 'internal')
        ], limit=1)
    
        if not location:
            # Create new location for distributor
            location = self.env['stock.location'].create({
                'name': location_name,
                'location_id': self.env.ref('stock.stock_location_locations').id,
                'usage': 'internal',
                # Store distributor reference in a custom field or use naming convention
            })
    
        return location


class DistributorPurchaseOrderLine(models.Model):
    _name = 'distributor.purchase.order.line'
    _description = 'Distributor Purchase Order Line'

    order_id = fields.Many2one(
        'distributor.purchase.order', 
        string='Order Reference', 
        required=True, 
        ondelete='cascade'
    )
    
    product_id = fields.Many2one(
        'product.product', 
        string='Product', 
        required=True,
        domain=[('type', '=', 'product')]
    )
    
    quantity = fields.Float(
        string='Quantity', 
        required=True, 
        default=1.0
    )
    
    unit_price = fields.Float(
        string='Unit Price', 
        required=True
    )
    
    subtotal = fields.Float(
        string='Subtotal', 
        compute='_compute_subtotal',
        store=True
    )

    # =====================================================
    # MANUAL SHIPMENT TRACKING (from purchase_manual_shipment)
    # =====================================================
    manual_shipped_qty = fields.Float(
        string='Manual Shipped Qty',
        digits='Product Unit of Measure',
        help='Actual quantity shipped',
        copy=False,
    )

    qty_diff_manual = fields.Float(
        string='Shipment Variance',
        compute='_compute_qty_diff_manual',
        store=True,
        digits='Product Unit of Measure',
        help='Difference between ordered and manually shipped quantity',
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
    )

    adjustment_date = fields.Datetime(
        string='Adjustment Date',
        copy=False,
        readonly=True,
    )

    adjustment_user_id = fields.Many2one(
        'res.users',
        string='Adjusted By',
        copy=False,
        readonly=True,
    )

    line_shipment_status = fields.Selection([
        ('pending', 'Pending'),
        ('partial', 'Partially Shipped'),
        ('shipped', 'Fully Shipped'),
    ], string='Line Status', compute='_compute_line_shipment_status', store=True)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

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
            if line.manual_shipped_qty and line.manual_shipped_qty < 0:
                raise ValidationError(
                    "Manual shipped quantity cannot be negative for product '{}'.".format(
                        line.product_id.name or ''
                    )
                )
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set default unit price when product changes"""
        if self.product_id:
            self.unit_price = self.product_id.list_price

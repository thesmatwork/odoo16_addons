from odoo import models, fields, api
from datetime import datetime, timedelta


class GenericTask(models.Model):
    _name = 'generic.task'
    _description = 'Generic Task System'
    _order = 'priority desc, due_date asc'
    _rec_name = 'title'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Information
    title = fields.Char(string='Title', required=True, tracking=True)
    description = fields.Html(string='Description')

    # Categorization & Usage
    category_id = fields.Many2one('task.category', string='Category', required=False, tracking=True)
    use_case = fields.Char(string='Use Case', help="Specific use case identifier (e.g., 'sales_todo')")
    tags = fields.Char(string='Tags', help="Comma-separated tags for filtering")

    # Priority & Status
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium', required=True, tracking=True)

    status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold')
    ], default='pending', required=True, tracking=True)

    # Dates
    due_date = fields.Datetime(string='Due Date', tracking=True)
    start_date = fields.Datetime(string='Start Date')
    completed_date = fields.Datetime(string='Completed Date', readonly=True)
    estimated_hours = fields.Float(string='Estimated Hours')

    # Users
    assigned_user_id = fields.Many2one('res.users', string='Assigned To', required=True, tracking=True)
    created_by_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    reviewer_id = fields.Many2one('res.users', string='Reviewer')

    # Generic Relations
    related_model = fields.Char(string='Related Model')
    related_record_id = fields.Integer(string='Related Record ID')
    related_record_name = fields.Char(string='Related Record Name', compute='_compute_related_record_name')

    # Common Relations
    partner_id = fields.Many2one('res.partner', string='Contact/Customer')

    # Tracking & Progress
    is_overdue = fields.Boolean(string='Overdue', compute='_compute_overdue', store=True)
    progress = fields.Integer(string='Progress %', default=0, tracking=True)

    # Custom Fields
    custom_data = fields.Json(string='Custom Data', help="Store any additional data as JSON")

    @api.depends('related_model', 'related_record_id')
    def _compute_related_record_name(self):
        for record in self:
            if record.related_model and record.related_record_id:
                try:
                    related_record = self.env[record.related_model].browse(record.related_record_id)
                    if related_record.exists():
                        record.related_record_name = related_record.display_name
                    else:
                        record.related_record_name = f"Deleted {record.related_model} #{record.related_record_id}"
                except Exception:
                    record.related_record_name = f"Invalid {record.related_model} #{record.related_record_id}"
            else:
                record.related_record_name = False

    @api.depends('due_date', 'status')
    def _compute_overdue(self):
        now = fields.Datetime.now()
        for record in self:
            if record.due_date and record.status not in ['completed', 'cancelled']:
                record.is_overdue = now > record.due_date
            else:
                record.is_overdue = False

    # --- Button Actions ---
    def mark_completed(self):
        self.write({'status': 'completed', 'completed_date': fields.Datetime.now(), 'progress': 100})
        return True

    def mark_in_progress(self):
        self.write({'status': 'in_progress'})
        if not self.start_date:
            self.start_date = fields.Datetime.now()
        return True

    def open_related_record(self):
        """Button: Open the related record"""
        self.ensure_one()
        if not self.related_model or not self.related_record_id:
            return False
        return {
            'name': 'Related Record',
            'type': 'ir.actions.act_window',
            'res_model': self.related_model,
            'res_id': self.related_record_id,
            'view_mode': 'form',
            'target': 'current',
        }

    # --- API Methods ---
    @api.model
    def get_tasks_by_criteria(self, **kwargs):
        domain = []

        if kwargs.get('use_case'):
            domain.append(('use_case', '=', kwargs['use_case']))
        if kwargs.get('category_code'):
            category = self.env['task.category'].search([('code', '=', kwargs['category_code'])], limit=1)
            if category:
                domain.append(('category_id', '=', category.id))
        if kwargs.get('user_id'):
            domain.append(('assigned_user_id', '=', kwargs['user_id']))
        if kwargs.get('status'):
            domain.append(('status', '=', kwargs['status']))
        if kwargs.get('priority'):
            domain.append(('priority', '=', kwargs['priority']))
        if kwargs.get('overdue_only'):
            domain.append(('is_overdue', '=', True))
        if kwargs.get('due_date_from'):
            domain.append(('due_date', '>=', kwargs['due_date_from']))
        if kwargs.get('due_date_to'):
            domain.append(('due_date', '<=', kwargs['due_date_to']))

        tasks = self.search(domain, limit=kwargs.get('limit', 100))
        return tasks.read([
            'id', 'title', 'description', 'category_id', 'use_case', 'tags',
            'priority', 'status', 'due_date', 'start_date', 'assigned_user_id',
            'created_by_id', 'partner_id', 'is_overdue', 'progress',
            'related_model', 'related_record_id', 'related_record_name',
            'custom_data', 'create_date', 'write_date'
        ])

    @api.model
    def create_task(self, **kwargs):
        if kwargs.get('category_code') and not kwargs.get('category_id'):
            category = self.env['task.category'].search([('code', '=', kwargs['category_code'])], limit=1)
            if category:
                kwargs['category_id'] = category.id
            kwargs.pop('category_code', None)
        task = self.create(kwargs)
        return task.id

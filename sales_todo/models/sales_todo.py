from odoo import models, fields, api

class SalesTodo(models.Model):
    _name = 'sales.todo'
    _description = 'Sales Todo Items'
    _order = 'priority desc, due_date asc'
    _rec_name = 'title'

    title = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium', required=True)
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending', required=True)
    
    due_date = fields.Datetime(string='Due Date')
    completed_date = fields.Datetime(string='Completed Date', readonly=True)
    
    assigned_user_id = fields.Many2one('res.users', string='Assigned To', required=True)
    created_by_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    
    opportunity_id = fields.Many2one('crm.lead', string='Related Opportunity')
    partner_id = fields.Many2one('res.partner', string='Customer')
    
    is_overdue = fields.Boolean(string='Overdue', compute='_compute_overdue', store=True)
    progress = fields.Integer(string='Progress %', default=0)
    
    create_date = fields.Datetime(string='Created On', readonly=True)
    write_date = fields.Datetime(string='Last Updated', readonly=True)

    @api.depends('due_date', 'status')
    def _compute_overdue(self):
        for record in self:
            if record.due_date and record.status not in ['completed', 'cancelled']:
                record.is_overdue = fields.Datetime.now() > record.due_date
            else:
                record.is_overdue = False

    def mark_completed(self):
        self.write({
            'status': 'completed',
            'completed_date': fields.Datetime.now(),
            'progress': 100
        })
        return True

    def mark_in_progress(self):
        self.write({'status': 'in_progress'})
        return True

    @api.model
    def get_user_todos(self, user_id=None, status=None):
        domain = []
        if user_id:
            domain.append(('assigned_user_id', '=', user_id))
        if status:
            domain.append(('status', '=', status))
        return self.search(domain).read([
            'id', 'title', 'description', 'priority', 'status',
            'due_date', 'assigned_user_id', 'created_by_id',
            'opportunity_id', 'partner_id', 'is_overdue', 'progress'
        ])

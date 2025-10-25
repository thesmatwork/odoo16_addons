from odoo import models, fields, api

class SalesMessage(models.Model):
    _name = 'sales.message'
    _description = 'Sales Messages'
    _order = 'create_date desc'
    _rec_name = 'title'

    title = fields.Char(string='Title', required=True)
    content = fields.Html(string='Content', required=True)
    
    message_type = fields.Selection([
        ('info', 'Information'),
        ('task', 'Task Assignment'),
        ('urgent', 'Urgent Notice'),
        ('announcement', 'Announcement'),
        ('reminder', 'Reminder')
    ], default='info', required=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium', required=True)
    
    sender_id = fields.Many2one('res.users', string='Sender', default=lambda self: self.env.user)
    recipient_ids = fields.Many2many('res.users', string='Recipients')
    
    is_read = fields.Boolean(string='Read', default=False)
    read_date = fields.Datetime(string='Read Date')
    
    scheduled_date = fields.Datetime(string='Scheduled For')
    is_scheduled = fields.Boolean(string='Is Scheduled', compute='_compute_is_scheduled')
    
    todo_id = fields.Many2one('sales.todo', string='Related Todo')
    opportunity_id = fields.Many2one('crm.lead', string='Related Opportunity')
    
    @api.depends('scheduled_date')
    def _compute_is_scheduled(self):
        for record in self:
            record.is_scheduled = bool(record.scheduled_date and record.scheduled_date > fields.Datetime.now())

    def mark_as_read(self):
        self.write({
            'is_read': True,
            'read_date': fields.Datetime.now()
        })
        return True

    @api.model
    def get_user_messages(self, user_id=None, unread_only=False):
        domain = []
        if user_id:
            domain.append(('recipient_ids', 'in', [user_id]))
        if unread_only:
            domain.append(('is_read', '=', False))
        return self.search(domain).read([
            'id', 'title', 'content', 'message_type', 'priority',
            'sender_id', 'is_read', 'read_date', 'create_date',
            'todo_id', 'opportunity_id'
        ])

    @api.model
    def send_message_to_users(self, title, content, user_ids, message_type='info', priority='medium'):
        message = self.create({
            'title': title,
            'content': content,
            'message_type': message_type,
            'priority': priority,
            'recipient_ids': [(6, 0, user_ids)]
        })
        return message.id

from odoo import models, fields, api


class GenericMessage(models.Model):
    _name = 'generic.message'
    _description = 'Generic Message System'
    _order = 'create_date desc'
    _rec_name = 'title'
    _inherit = ['mail.thread']

    title = fields.Char(string='Title', required=True)
    content = fields.Html(string='Content', required=True)
    use_case = fields.Char(string='Use Case')
    tags = fields.Char(string='Tags')

    message_type = fields.Selection([
        ('info', 'Information'),
        ('task', 'Task Assignment'),
        ('urgent', 'Urgent Notice'),
        ('announcement', 'Announcement'),
        ('reminder', 'Reminder'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('custom', 'Custom')
    ], default='info', required=True)

    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium', required=True)

    sender_id = fields.Many2one('res.users', string='Sender', default=lambda self: self.env.user, readonly=True)
    recipient_ids = fields.Many2many('res.users', string='Recipients', required=True)

    read_status_ids = fields.One2many('generic.message.read.status', 'message_id', string='Read Status')

    scheduled_date = fields.Datetime(string='Scheduled For')
    expiry_date = fields.Datetime(string='Expires On')
    is_scheduled = fields.Boolean(string='Is Scheduled', compute='_compute_is_scheduled')
    is_expired = fields.Boolean(string='Is Expired', compute='_compute_is_expired')

    related_model = fields.Char(string='Related Model')
    related_record_id = fields.Integer(string='Related Record ID')
    related_record_name = fields.Char(string='Related Record Name', compute='_compute_related_record_name')

    task_id = fields.Many2one('generic.task', string='Related Task')
    partner_id = fields.Many2one('res.partner', string='Related Contact')

    custom_data = fields.Json(string='Custom Data')

    total_recipients = fields.Integer(string='Total Recipients', compute='_compute_recipient_stats')
    read_count = fields.Integer(string='Read Count', compute='_compute_recipient_stats')
    unread_count = fields.Integer(string='Unread Count', compute='_compute_recipient_stats')

    # --- Compute fields ---
    @api.depends('scheduled_date')
    def _compute_is_scheduled(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_scheduled = bool(record.scheduled_date and record.scheduled_date > now)

    @api.depends('expiry_date')
    def _compute_is_expired(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_expired = bool(record.expiry_date and record.expiry_date < now)

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

    @api.depends('recipient_ids', 'read_status_ids')
    def _compute_recipient_stats(self):
        for record in self:
            record.total_recipients = len(record.recipient_ids)
            record.read_count = len(record.read_status_ids.filtered('is_read'))
            record.unread_count = record.total_recipients - record.read_count

    # --- Overrides ---
    @api.model
    def create(self, vals):
        message = super().create(vals)
        for recipient in message.recipient_ids:
            self.env['generic.message.read.status'].create({
                'message_id': message.id,
                'user_id': recipient.id,
                'is_read': False
            })
        return message

    # --- Button Actions ---
    def mark_as_read_for_user(self, user_id=None):
        if not user_id:
            user_id = self.env.user.id
        status = self.read_status_ids.filtered(lambda r: r.user_id.id == user_id)
        if status:
            status.write({'is_read': True, 'read_date': fields.Datetime.now()})
        return True

    def action_view_recipients(self):
        """Button: Open recipient list"""
        return {
            'name': 'Recipients',
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.recipient_ids.ids)],
            'target': 'new',
        }

    def action_view_read_status(self):
        """Button: Open read status"""
        return {
            'name': 'Read Status',
            'type': 'ir.actions.act_window',
            'res_model': 'generic.message.read.status',
            'view_mode': 'tree,form',
            'domain': [('message_id', '=', self.id)],
            'target': 'new',
        }

    # --- API Methods ---
    @api.model
    def get_messages_by_criteria(self, **kwargs):
        domain = []
        if kwargs.get('use_case'):
            domain.append(('use_case', '=', kwargs['use_case']))
        if kwargs.get('user_id'):
            domain.append(('recipient_ids', 'in', [kwargs['user_id']]))
        if kwargs.get('user_id') and kwargs.get('unread_only'):
            unread_message_ids = self.env['generic.message.read.status'].search([
                ('user_id', '=', kwargs['user_id']),
                ('is_read', '=', False)
            ]).mapped('message_id').ids
            domain.append(('id', 'in', unread_message_ids))
        if kwargs.get('message_type'):
            domain.append(('message_type', '=', kwargs['message_type']))
        if kwargs.get('priority'):
            domain.append(('priority', '=', kwargs['priority']))
        if kwargs.get('active_only'):
            now = fields.Datetime.now()
            domain.append('|')
            domain.append(('expiry_date', '=', False))
            domain.append(('expiry_date', '>', now))

        messages = self.search(domain, limit=kwargs.get('limit', 100))
        result = messages.read([
            'id', 'title', 'content', 'use_case', 'tags', 'message_type',
            'priority', 'sender_id', 'scheduled_date', 'expiry_date',
            'related_model', 'related_record_id', 'related_record_name',
            'task_id', 'partner_id', 'custom_data', 'create_date'
        ])
        if kwargs.get('user_id'):
            for msg_data in result:
                status = self.browse(msg_data['id']).read_status_ids.filtered(
                    lambda r: r.user_id.id == kwargs['user_id']
                )
                msg_data['is_read'] = status.is_read if status else False
                msg_data['read_date'] = status.read_date if status else False
        return result

    @api.model
    def send_message(self, **kwargs):
        if 'recipient_ids' in kwargs and isinstance(kwargs['recipient_ids'], list):
            kwargs['recipient_ids'] = [(6, 0, kwargs['recipient_ids'])]
        message = self.create(kwargs)
        return message.id


class GenericMessageReadStatus(models.Model):
    _name = 'generic.message.read.status'
    _description = 'Message Read Status per User'

    message_id = fields.Many2one('generic.message', string='Message', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', required=True)
    is_read = fields.Boolean(string='Is Read', default=False)
    read_date = fields.Datetime(string='Read Date')

    _sql_constraints = [
        ('unique_user_message', 'unique(message_id, user_id)', 'Read status must be unique per user per message!')
    ]

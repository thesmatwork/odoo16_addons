from odoo import models, fields, api

class TodoItem(models.Model):
    _name = 'sales.todo'
    _description = 'Sales Todo Item'
    _order = 'deadline asc'

    name = fields.Char(string='Task Name', required=True)
    description = fields.Text(string='Description')
    assigned_to = fields.Many2one('res.users', string='Assigned To')
    deadline = fields.Date(string='Deadline')
    is_done = fields.Boolean(string='Completed', default=False)
    priority = fields.Selection(
        [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        string='Priority', default='medium'
    )
    color = fields.Integer(string='Color Index')

    @api.onchange('is_done')
    def _onchange_is_done(self):
        if self.is_done:
            self.color = 10  # Green
        else:
            self.color = 0   # Default

    def action_mark_done(self):
        for record in self:
            record.is_done = True

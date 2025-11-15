from odoo import models, fields, api

class TaskCategory(models.Model):
    _name = 'task.category'
    _description = 'Task Categories'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True)
    code = fields.Char(string='Category Code', required=True, help="Unique identifier for this category")
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)

    # Appearance
    color = fields.Integer(string='Color Index', default=0)
    icon = fields.Char(string='Icon Class', help="FontAwesome icon class")

    # Configuration
    active = fields.Boolean(string='Active', default=True)
    default_priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium', string='Default Priority')

    # Usage tracking
    task_count = fields.Integer(string='Task Count', compute='_compute_task_count')

    @api.depends()
    def _compute_task_count(self):
        for record in self:
            record.task_count = self.env['generic.task'].search_count([
                ('category_id', '=', record.id)
            ])

    def action_view_tasks(self):
        """Smart button action to view tasks in this category"""
        self.ensure_one()
        return {
            'name': f'Tasks - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'generic.task',
            'view_mode': 'tree,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
        }

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Category code must be unique!')
    ]

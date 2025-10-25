from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    tagline = fields.Char(string="Tagline")

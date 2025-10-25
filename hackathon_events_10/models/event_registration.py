# -*- coding: utf-8 -*-
from odoo import models, fields


class EventRegistration(models.Model):
    _inherit = "event.registration"

    team_id = fields.Many2one(
        "event.team",
        string="Team",
        ondelete="set null",
        index=True,
    )

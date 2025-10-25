# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EventTeam(models.Model):
    _name = "event.team"
    _description = "Hackathon Team"
    _rec_name = "name"

    name = fields.Char(
        string="Team Name",
        required=True,
        help="Unique name for the team",
    )
    event_id = fields.Many2one(
        "event.event",
        string="Event",
        required=True,
        ondelete="restrict",
    )
    member_ids = fields.One2many(
        "event.registration",
        "team_id",
        string="Team Members",
    )

    _sql_constraints = [
        ("team_uniq_per_event",
         "unique(name, event_id)",
         "A team with this name already exists for this event.")
    ]

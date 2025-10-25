# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.event.controllers.main import EventController as BaseEventController


class EventController(BaseEventController):
    """
    Extend the confirmation route to handle team selection/creation
    for each attendee submitted from the website popup.
    """

    @http.route(
        ['/event/<model("event.event"):event>/registration/confirm'],
        type="http", auth="public", website=True, csrf=True
    )
    def event_registration_confirm(self, event, **post):
        # Let the standard flow create the registrations first
        res = request.env["website_event.event"]._process_attendee_registration(event, post)

        # Determine how many attendee rows were submitted by scanning counters 0..N
        counters = []
        i = 0
        while True:
            if f"{i}-name" in post or f"{i}-email" in post:
                counters.append(i)
                i += 1
            else:
                break

        if not counters:
            return res

        # Find the registrations created for THIS visitor and THIS event, most recent first
        visitor = request.env["website.visitor"]._get_visitor_from_request()
        Attendee = request.env["event.registration"].sudo()

        regs = Attendee.search(
            [("event_id", "=", event.id), ("visitor_id", "=", visitor.id)],
            order="id desc",
            limit=len(counters),
        )
        # The newest record corresponds to the last row; reverse to align 0..N
        regs = list(reversed(regs))

        Team = request.env["event.team"].sudo()
        for idx, reg in enumerate(regs):
            team_id_val = post.get(f"{idx}-team_id")
            team_name_val = (post.get(f"{idx}-team_name") or "").strip()

            if team_id_val:
                # link to existing team
                reg.write({"team_id": int(team_id_val)})
                continue

            if team_name_val:
                # find or create team for this event
                team = Team.search(
                    [("event_id", "=", event.id), ("name", "=", team_name_val)],
                    limit=1,
                )
                if not team:
                    team = Team.create({"name": team_name_val, "event_id": event.id})
                reg.write({"team_id": team.id})

        return res

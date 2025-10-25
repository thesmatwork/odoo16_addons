from odoo import http
from odoo.http import request
from odoo.addons.event.controllers.main import EventController as BaseEventController


class EventController(BaseEventController):

    def _prepare_registrant_fields(self, event, **post):
        """Extend to accept team_name from form."""
        values = super(EventController, self)._prepare_registrant_fields(event, **post)
        if event.is_event_team:
            values['team_name'] = post.get('team_name')
        return values

    def _process_registration_data(self, event, registration_data):
        """Extend registration pipeline to auto-create teams if only team_name given."""
        super(EventController, self)._process_registration_data(event, registration_data)
        if event.is_event_team:
            for registration in event.registration_ids:
                if registration.team_name and not registration.team_id:
                    registration._create_teams_from_registrations()

    @http.route(
        ['/event/<model("event.event"):event>/registration/confirm'],
        type='http', auth="public", website=True, csrf=True
    )
    def event_registration_confirm(self, event, **post):
        """
        Handle team_id (existing) or team_name (new) for ALL attendees.
        """
        # Let Odoo handle normal attendee creation first
        res = request.env['website_event.event']._process_attendee_registration(event, post)

        if event.is_event_team:
            Attendee = request.env['event.registration'].sudo()

            # Count attendees from posted data
            num_attendees = len([k for k in post.keys() if k.endswith('-name')])

            # Get the last N registrations created for this event
            registrations = Attendee.search(
                [('event_id', '=', event.id)],
                order="id desc",
                limit=num_attendees
            )

            # Registrations come in reverse order, so reverse them
            registrations = registrations[::-1]

            # Loop over each registration
            for idx, registration in enumerate(registrations):
                team_id = post.get(f'{idx}-team_id')
                team_name = post.get(f'{idx}-team_name')

                if team_id:
                    registration.write({'team_id': int(team_id)})
                elif team_name and not registration.team_id:
                    new_team = request.env['event.team'].sudo().create({
                        'team_name': team_name,   # ✅ FIXED
                        'event_id': event.id,
                    })
                    registration.write({'team_id': new_team.id})

        return res

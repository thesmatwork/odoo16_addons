# -*- coding: utf-8 -*-
{
    "name": "Hackathon v2.1",
    "version": "2.1",
    "depends": ["base", "event", "website", "website_event"],
    "author": "Your Name",
    "category": "Events",
    "summary": "Adds team registration and management for hackathons",
    "description": "Extends Odoo Event module for hackathon use with team functionality, including saving Team Name in registration form",
    "data": [
        "security/ir.model.access.csv",
        "views/event_team_views.xml",          # Team model views
        "views/event_registration_views.xml",  # Event registration form views
        "views/event_website_template.xml",    # Website template for Team Name input
    ],
    "installable": True,
    "application": True,
}

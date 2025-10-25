from odoo import http
from odoo.http import request

class SalesTodoAPI(http.Controller):

    @http.route('/sales_todo/api/todos', auth='user', type='json', methods=['POST'])
    def get_todos(self, user_id=None, status=None):
        todos = request.env['sales.todo'].sudo().get_user_todos(user_id, status)
        return {'todos': todos}

    @http.route('/sales_todo/api/messages', auth='user', type='json', methods=['POST'])
    def get_messages(self, user_id=None, unread_only=False):
        messages = request.env['sales.message'].sudo().get_user_messages(user_id, unread_only)
        return {'messages': messages}

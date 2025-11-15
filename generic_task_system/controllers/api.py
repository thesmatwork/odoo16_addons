from odoo import http
from odoo.http import request
import json
 
class GenericTaskAPI(http.Controller):
    
    @http.route('/api/tasks', type='json', auth='user', methods=['GET'], csrf=False)
    def get_tasks(self, *kwargs):
        """Get tasks for current user"""
        try:
            tasks = request.env['generic.task'].search([
                ('assigned_user_id', '=', request.env.user.id)
            ], limit=kwargs.get('limit', 50))
            
            return {
                'success': True,
                'tasks': tasks.read([
                    'id', 'title', 'description', 'priority', 'status', 
                    'due_date', 'category_id', 'is_overdue'
                ])
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/tasks/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_task(self, kwargs):
        """Create a new task"""
        try:
            task = request.env['generic.task'].create({
                'title': kwargs.get('title'),
                'description': kwargs.get('description'),
                'category_code': kwargs.get('category_code', 'general'),
                'priority': kwargs.get('priority', 'medium'),
                'assigned_user_id': kwargs.get('assigned_user_id', request.env.user.id),
                'use_case': kwargs.get('use_case'),
            })
            
            return {
                'success': True,
                'task_id': task.id
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/messages', type='json', auth='user', methods=['GET'], csrf=False)
    def get_messages(self, *kwargs):
        """Get messages for current user"""
        try:
            messages = request.env['generic.message'].get_messages_by_criteria(
                user_id=request.env.user.id,
                unread_only=kwargs.get('unread_only', False),
                limit=kwargs.get('limit', 50)
            )
            
            return {
                'success': True,
                'messages': messages
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

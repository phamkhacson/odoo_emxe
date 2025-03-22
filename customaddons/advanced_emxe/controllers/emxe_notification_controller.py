from odoo import http
from odoo import fields, models, api
from odoo.http import request, _logger
import re
import json
from urllib.parse import urlencode
from odoo.exceptions import UserError
import requests
from datetime import datetime, timedelta
import logging


def _create_flutter_log(env, name=None, type=None, description=None):
    """
    Logging for api
    param
    type: [request, response, error].
    """
    env['emxe.flutter.log'].sudo().create({
        'name': name,
        'type': type,
        'description': description,
    })


def strip_html_tags(html):
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', html)
    text.replace('\n', '')
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text


class EMXENotificationController(http.Controller):

    @http.route('/emxe_api/add_registration_id', auth='user', csrf=False, type='json')
    def emxe_add_registration_id(self, **kw):
        try:
            _create_flutter_log(request.env, name='add_registration_id', description=str(kw), type='request')
            user = request.env.user
            if kw.get('registration_id'):
                reg = request.env['emxe.mobile.registration.token'].sudo().search(
                    [('token', '=', kw.get('registration_id'))], limit=1)
                if not reg:
                    request.env['emxe.mobile.registration.token'].sudo().create(
                        {
                            'user_id': user.id,
                            'token': kw.get('registration_id'),
                        }
                    )
                else:
                    reg.sudo().write({'user_id': user.id})
                return {
                    "status": "success",
                    "code": 200,
                    "message": "Đăng ký thành công",
                    "data": {
                        "success": True
                    }
                }
        except Exception as e:
            _create_flutter_log(request.env, name='add_registration_id', description=str(e), type='error')
            return {
                'status': 'fail',
                'code': 400,
                'message': e,
            }

    @http.route('/emxe_api/get_notification_message', auth='user', csrf=False, type='json')
    def emxe_get_notification_message(self, **kw):
        try:
            _create_flutter_log(request.env, name='get_notification_message', description=str(kw), type='request')
            user = request.env.user
            message_list = []
            offset = kw.get('index') if kw.get('index') else 0
            limit = kw.get('offset') if kw.get('offset') else 80
            if user.partner_id:
                message = request.env['mail.message'].search(
                    [('partner_ids', 'in', user.partner_id.id), ('message_type', '=', 'notification'),
                     ('model', 'in', ['hc.trip'])], offset=offset, limit=limit, order='id desc')
                print(message)
                if len(message) > 0:
                    for mess in message:
                        val = {
                            'create_on': mess.create_date,
                            'message_id': mess.id,
                            'type': 'payment' if 'của bạn đã được hoàn thành' in mess.body else 'trip',
                            'message_name': 'Thông báo',
                            'message_body': strip_html_tags(mess.body) if mess.body else None,
                            'res_id': mess.res_id,
                        }
                        message_list.append(val)
            return {
                "status": "success",
                "code": 200,
                "message": "success",
                "data": message_list
            }


        except Exception as e:
            _create_flutter_log(request.env, name='get_notification_message', description=str(e), type='error')
            return {
                'status': 'fail',
                'code': 400,
                'message': e,
            }




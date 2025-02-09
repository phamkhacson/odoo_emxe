# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging


import odoo
import odoo.modules.registry
from odoo import http
from odoo.modules import module
from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo.http import request
from odoo.tools.translate import _


_logger = logging.getLogger(__name__)


class Session(http.Controller):

    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        if not http.db_filter([db]):
            raise AccessError("Database not found.")
        try:
            phone = int(login)
        except Exception as ex:
            phone = False
        if phone:
            user = request.env['res.users'].sudo().search([('phone', '=', login)], limit=1)
            if user:
                login = user.login
        try:
            pre_uid = request.session.authenticate(db, login, password)
        except Exception as ex:
            return {
                "status": "error",
                "error": {
                    "code": 401,
                    "message": "Tên đăng nhập hoặc mật khẩu không chính xác"
                }
            }

        if pre_uid != request.session.uid:
            # Crapy workaround for unupdatable Odoo Mobile App iOS (Thanks Apple :@) and Android
            # Correct behavior should be to raise AccessError("Renewing an expired session for user that has multi-factor-authentication is not supported. Please use /web/login instead.")
            return {'uid': None}

        request.session.db = db
        registry = odoo.modules.registry.Registry(db)
        with registry.cursor() as cr:
            env = odoo.api.Environment(cr, request.session.uid, request.session.context)
            if not request.db:
                # request._save_session would not update the session_token
                # as it lacks an environment, rotating the session myself
                http.root.session_store.rotate(request.session, env)
                request.future_response.set_cookie(
                    'session_id', request.session.sid,
                    max_age=http.SESSION_LIFETIME, httponly=True
                )
            return env['ir.http'].session_info()
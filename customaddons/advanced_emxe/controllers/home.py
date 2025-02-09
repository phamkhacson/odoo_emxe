# -*- coding: utf-8 -*-
from odoo.addons.web.controllers.home import Home
import werkzeug
from odoo import http
from odoo.http import request


class HomeController(Home):

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        if request.session.uid:
            if 'debug=' in request.httprequest.full_path:
                if len(request.httprequest.full_path) > 11:
                    debug_position = request.httprequest.full_path.index('debug=')
                    if request.httprequest.full_path[debug_position + 6] != '#':
                        if not request.env.ref('base.group_system').id in request.env['res.users'].sudo().browse(request.session.uid).groups_id.ids:
                            return werkzeug.utils.redirect('/web?debug=', 303)
        return super(HomeController, self).web_client(kw)

# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import jinja2
import os
import babel.numbers


def number_format(value):
    return babel.numbers.format_decimal(value)


path = os.path.realpath(os.path.join(os.path.dirname(__file__), '../html'))
loader = jinja2.FileSystemLoader(path)
jinja_env = jinja2.Environment(loader=loader, autoescape=True)
jinja_env.filters["json"] = json.dumps
jinja_env.filters["number_format"] = number_format


class DriverExtensions(http.Controller):

    @http.route('/driver/cost/register', type='http', auth="user")
    def register_cost(self, **kw):
        try:
            template = jinja_env.get_template('register_cost.html')
            trip_records = request.env['hc.trip'].sudo().search([('driver_id', '=', request.env.user.id)])
            trips = []
            for trip in trip_records:
                trip_display_name = trip.hc_code
                location = []
                if trip.pick_up_place:
                    location.append(trip.pick_up_place)
                if trip.destination:
                    location.append(trip.destination)
                if len(location) > 0:
                    trip_display_name += ' - ' + ' - '.join(location)
                trips.append({'id': trip.id, 'name': trip_display_name})
            res = template.render({"trips": trips})
            return res
        except Exception as e:
            return 'Có lỗi xảy ra. Vui lòng liên hệ quản trị viên hệ thống!'

    @http.route('/driver/cost/submit', type='json', auth="user", cors='*')
    def submit_cost(self, kwargs):
        try:
            trip_id = kwargs.get('trip_id', False)
            if trip_id:
                trip = request.env['hc.trip'].sudo().search([('id', '=', trip_id)])
                if trip and trip.driver_id == request.env.user:
                    pass
                    #todo
            print(request.env.user.id)
            print(kwargs)
        except Exception as e:
            return 'Có lỗi xảy ra. Vui lòng liên hệ quản trị viên hệ thống!'



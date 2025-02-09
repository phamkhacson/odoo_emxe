# -*- coding: utf-8 -*-

from odoo import models, fields


class HcTripPaidCost(models.Model):
    _name = 'hc.trip.paid.cost'
    _description = 'Các khoản đã chi'
    _rec_name = 'name'

    note = fields.Char(string="Ghi chú")
    name = fields.Char(string="Tên")
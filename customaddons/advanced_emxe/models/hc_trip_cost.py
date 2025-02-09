# -*- coding: utf-8 -*-

from odoo import models, fields


class HcTripCost(models.Model):
    _name = 'hc.trip.cost'
    _description = 'Các khoản chi'
    _rec_name = 'name'

    type_id = fields.Many2one('hc.trip.cost.type', string='Loại chi phí')
    note = fields.Char(string="Ghi chú")
    name = fields.Char(string="Tên")
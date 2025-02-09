# -*- coding: utf-8 -*-

from odoo import models, fields


class HcTripCostType(models.Model):
    _name = 'hc.trip.cost.type'
    _description = 'Loại chi phí'
    _rec_name = 'name'

    name = fields.Char(string="Tên chi phí")
    note = fields.Char(string="Ghi chú")
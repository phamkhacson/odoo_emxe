# -*- coding: utf-8 -*-

from odoo import models, fields


class HcTripSeries(models.Model):
    _name = 'hc.trip.series'
    _description = 'Series chuyến'
    _rec_name = 'name'

    name = fields.Char(string="Tên")
    trip_stage_ids = fields.Many2many('hc.trip.stage', string="Danh sách chặng")
    source_place = fields.Char(string="Điểm tiễn")
# -*- coding: utf-8 -*-

from odoo import models, fields


class HcTripStage(models.Model):
    _name = 'hc.trip.stage'
    _description = 'Chặng đi'
    _rec_name = 'name'

    pick_up_place = fields.Char(string="Điểm đón")
    destination = fields.Char(string="Điểm đến")
    km_count = fields.Float(string="Số KM mặc định")
    note = fields.Char(string="Ghi chú")
    name = fields.Char('Tên chặng', compute="_compute_name")

    def _compute_name(self):
        for rec in self:
            name_list = []
            if rec.pick_up_place:
                name_list.append(rec.pick_up_place)
            if rec.destination:
                name_list.append(rec.destination)
            name = " - ".join(name_list)
            rec.sudo().name = name

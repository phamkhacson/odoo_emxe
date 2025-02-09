# -*- coding: utf-8 -*-

from odoo import models, fields


class HcRepairManagement(models.Model):
    _name = 'hc.repair.management'
    _description = 'Quản lý sửa chữa'
    _rec_name = 'vehicle_id'

    date = fields.Date(string="Ngày")
    amount = fields.Float(string="Tiền")
    vehicle_id = fields.Many2one('hc.vehicle', string="Xe")
    note = fields.Char(string="Ghi chú")
    user_id = fields.Many2one('res.users', string="Người nhập")

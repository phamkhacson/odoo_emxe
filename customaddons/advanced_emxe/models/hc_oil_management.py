# -*- coding: utf-8 -*-

from odoo import models, fields


class HcOilManagement(models.Model):
    _name = 'hc.oil.management'
    _description = 'Quản lý dầu'
    _rec_name = 'vehicle_id'

    date = fields.Date(string="Ngày")
    liter = fields.Float(string="Lít")
    price = fields.Float(string="Đơn giá")
    amount = fields.Float(string="Thành tiền")
    start_km = fields.Float(string="Km đầu")
    end_km = fields.Float(string="Km chốt")
    run_km = fields.Float(string="Km chạy")
    vehicle_id = fields.Many2one('hc.vehicle', string="Xe")
    mtt = fields.Char(string="MTT")
    user_id = fields.Many2one('res.users', string="Người nhập")

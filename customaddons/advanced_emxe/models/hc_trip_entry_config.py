# -*- coding: utf-8 -*-

from odoo import models, fields


class HcTripEntryConfig(models.Model):
    _name = 'hc.trip.entry.config'
    _description = 'Cấu hình các khoản thu/chi, đã thu/chi, chi phí vận hành nội bộ, khoản lái xe đã chi'
    _rec_name = 'name'

    type_id = fields.Many2one('hc.trip.cost.type', string='Loại chi phí', help="Dùng cho cấu hình các khoản chi")
    note = fields.Char(string="Ghi chú")
    name = fields.Char(string="Tên")
    vat = fields.Float(string="VAT(%)", help="Dùng cho cấu hình các khoản thu")
    is_freight_cost = fields.Boolean(string="Là cước vận tải", default=False, help="Dùng cho cấu hình các khoản thu")
    entry_type = fields.Selection([('cost', 'Khoản chi'), ('paid_cost', 'Khoản đã chi'), ('income', 'Khoản thu'), ('payment_income', 'Khoản đã thu'), ('operation_cost', 'Chi phí vận hành nội bộ'), ('driver_cost', 'Khoản lái xe đã chi')], string="Loại phát sinh")
    sequence = fields.Integer(string="Thứ tự hiển thị", default=99)
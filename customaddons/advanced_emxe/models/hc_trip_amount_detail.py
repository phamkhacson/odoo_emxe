# -*- coding: utf-8 -*-

from odoo import models, fields


class HcTripAmountDetail(models.Model):
    _name = 'hc.trip.amount.detail'
    _description = 'Các khoản tiền'

    income_id = fields.Many2one('hc.trip.entry.config', string='Khoản thu')
    payment_income_id = fields.Many2one('hc.trip.entry.config', string='Khoản đã thu')
    income_record_id = fields.Many2one('hc.trip')
    income_payment_record_id = fields.Many2one('hc.trip')
    cost_id = fields.Many2one('hc.trip.entry.config', string='Khoản chi')
    paid_cost_id = fields.Many2one('hc.trip.entry.config', string='Khoản đã chi')
    cost_record_id = fields.Many2one('hc.trip')
    cost_payment_record_id = fields.Many2one('hc.trip')
    price = fields.Float(string="Đơn giá")
    amount = fields.Float(string="Thành tiền", compute='_compute_amount')
    payment_amount = fields.Float(string="Số tiền")
    qty = fields.Float(string="Số lượng")
    note = fields.Char(string="Ghi chú")
    operation_cost_record_id = fields.Many2one('hc.trip')
    operation_cost_id = fields.Many2one('hc.trip.entry.config', string="Khoản chi")
    driver_cost_id = fields.Many2one('hc.trip.entry.config', string="Khoản chi")
    driver_cost_record_id = fields.Many2one('hc.trip')
    operation_cost_price = fields.Float(string="Số tiền")
    img_note = fields.Binary('Hình ảnh')

    def _compute_amount(self):
        for rec in self:
            rec.sudo().amount = rec.price * rec.qty
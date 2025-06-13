# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.populate import compute


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
    payer = fields.Selection([
        ('driver', 'Tài xế'),
        ('driver_advance', 'Tài xế tạm ứng'),
    ], string="Người trả", default='driver')
    sequence = fields.Integer(string="Thứ tự hiển thị", compute='_compute_sequence')

    def _compute_sequence(self):
        for rec in self:
            rec.sequence = rec.income_id.sequence if rec.income_id else rec.payment_income_id.sequence if rec.payment_income_id else rec.cost_id.sequence if rec.cost_id else rec.paid_cost_id.sequence if rec.paid_cost_id else rec.operation_cost_id.sequence if rec.operation_cost_id else rec.driver_cost_id.sequence if rec.driver_cost_id else 99

    @api.depends('price', 'qty')
    def _compute_amount(self):
        for rec in self:
            rec.sudo().amount = rec.price * rec.qty
# -*- coding: utf-8 -*-

from odoo import models, fields


class HcTripPaymentIncome(models.Model):
    _name = 'hc.trip.payment.income'
    _description = 'Các khoản đã thu'
    _rec_name = 'name'

    note = fields.Char(string="Ghi chú")
    name = fields.Char(string="Tên")
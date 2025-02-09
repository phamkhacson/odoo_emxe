# -*- coding: utf-8 -*-

from odoo import models, fields


class HcBankAccount(models.Model):
    _name = 'hc.bank.account'
    _description = 'Tài khoản ngân hàng'
    _rec_name = 'name'

    name = fields.Char(string="Số tài khoản")
    bank_name = fields.Char(string="Ngân hàng")
    dealer_id = fields.Many2one('hc.dealer', string='Đại lý')

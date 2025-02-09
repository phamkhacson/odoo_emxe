# -*- coding: utf-8 -*-

from odoo import models, fields


class HcDealer(models.Model):
    _name = 'hc.dealer'
    _description = 'Đại lý'
    _rec_name = 'name'

    name = fields.Char(string="Tên đại lý")
    company_name = fields.Char(string="Tên công ty")
    address = fields.Char(string="Địa chỉ")
    phone = fields.Char(string="Số điện thoại")
    tax = fields.Char(string="Mã số thuế")
    email = fields.Char(string="Email")
    related_user_ids = fields.Many2many('res.users', string="Danh sách người đại diện")
    bank_account_ids = fields.One2many('hc.bank.account', 'dealer_id', string="Tài khoản ngân hàng")

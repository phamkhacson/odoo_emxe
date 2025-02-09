# -*- coding: utf-8 -*-

from odoo import models, fields


class HcExecutiveGroup(models.Model):
    _name = 'hc.executive.group'
    _description = 'Nhóm điều hành'
    _rec_name = 'name'

    name = fields.Char(string="Tên")
    dealer_id = fields.Many2one('hc.dealer', 'Đại lý')
    operator_id = fields.Many2one('res.users', 'Điều hành')
    accountant_id = fields.Many2one('res.users', 'Kế toán')

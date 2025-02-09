# -*- coding: utf-8 -*-

from odoo import models, fields


class HcOperationCost(models.Model):
    _name = 'hc.operation.cost'
    _description = 'Chi phí vận hành nội bộ'
    _rec_name = 'name'

    name = fields.Char(string="Tên")
    note = fields.Char(string="Ghi chú")

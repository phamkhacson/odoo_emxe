# -*- coding: utf-8 -*-

from odoo import models, fields


class HcDriverCost(models.Model):
    _name = 'hc.driver.cost'
    _description = 'Chi phí lái xe đã chi'
    _rec_name = 'name'

    name = fields.Char(string="Tên")
    note = fields.Char(string="Ghi chú")

# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class HcTripIncome(models.Model):
    _name = 'hc.trip.income'
    _description = 'Các khoản thu'
    _rec_name = 'name'

    note = fields.Char(string="Ghi chú")
    name = fields.Char(string="Tên")
    vat = fields.Float(string="VAT(%)")
    is_freight_cost = fields.Boolean(string="Là cước vận tải", default=False)

    @api.constrains('is_freight_cost')
    def _check_is_freight_cost_constrain(self):
        for rec in self:
            if rec.is_freight_cost:
                freight_cost_exists = rec.env['hc.trip.income'].sudo().search([('is_freight_cost', '=', True), ('id', '!=', rec.id)])
                if freight_cost_exists:
                    raise UserError('Đã tồn tại bản ghi cước vận tải')
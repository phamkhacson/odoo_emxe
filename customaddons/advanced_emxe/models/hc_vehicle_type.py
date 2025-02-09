# -*- coding: utf-8 -*-

from odoo import models, fields


class HcVehicleType(models.Model):
    _name = 'hc.vehicle.type'
    _description = 'Loại xe'
    _rec_name = 'name'

    name = fields.Char(string="Tên loại xe")
    seat_count = fields.Integer(string="Số ghế")
    driver_salary_percent = fields.Float(string="% lương lái xe")

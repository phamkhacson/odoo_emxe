# -*- coding: utf-8 -*-

from odoo import models, fields


class HcVehicle(models.Model):
    _name = 'hc.vehicle'
    _description = 'Xe'
    _rec_name = 'license_plate'

    license_plate = fields.Char(string="Biển kiểm soát")
    type = fields.Many2one('hc.vehicle.type', string="Loại xe")
    own_vehicle_id = fields.Many2one('hc.transport.vendor', string="Nhà xe")
    driver_id = fields.Many2one('res.users', string="Tài xế")
    driver_ids = fields.Many2many('res.users', string="Tài xế")
    state = fields.Selection([('available', 'Đang trống'), ('process', 'Đang trong chuyến')], string="Trạng thái", compute='_compute_process_data')
    process_trip_id = fields.Many2one('hc.trip', 'Chuyến đang xử lý', compute='_compute_process_data')
    fuel_consumption = fields.Float(string="Mức tiêu thụ (lít/100km)")
    inspection_date = fields.Date(string="Hạn đăng kiểm")
    def _compute_process_data(self):
        for rec in self:
            trips = rec.env['hc.trip'].search([('vehicle_id', '=', rec.id), ('state', 'in', ['waiting', 'processing'])])
            state = 'available'
            process_trip_id = False
            if len(trips) > 0:
                state = 'process'
                process_trip_id = trips[0].id
            rec.sudo().state = state
            rec.sudo().process_trip_id = process_trip_id

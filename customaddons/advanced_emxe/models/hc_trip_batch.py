# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields, api
from datetime import datetime, timedelta

from odoo.exceptions import UserError
from odoo.fields import One2many


class HcTripBatch(models.Model):
    _name = 'hc.trip.batch'
    _description = 'Chuyến xe gộp'
    _rec_name = 'hc_code'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    hc_code = fields.Char(string="Code HC", copy=False)
    state = fields.Selection([('draft', 'Khai báo chuyến'), ('confirm', 'Đã điều chuyến')], string="Trạng thái", default='draft')
    is_common_info = fields.Boolean(string="Chỉnh sửa chi tiết", default=True)
    transport_vendor_id = fields.Many2one('hc.transport.vendor', string="Nhà xe")
    dealer_id = fields.Many2one('hc.dealer', string="Đại lý")
    vehicle_id = fields.Many2one('hc.vehicle', string="Xe")
    driver_id = fields.Many2one('res.users', string="Tài xế", related="vehicle_id.driver_id", store=True)
    driver_phone = fields.Char(string="SĐT tài xế", related="driver_id.phone")
    hc_trip_ids = One2many('hc.trip', 'batch_id', string="Lịch trình")

    def button_confirm(self):
        self.state = 'confirm'
        message = f'Đã điều chuyến xe gộp mã: {self.hc_code}'
        self.message_post(body=message, message_type='comment')
        # confirm only the trips that are in draft state
        draft_trip_ids = self.hc_trip_ids.filtered(lambda trip: trip.state == 'draft')
        if draft_trip_ids:
            draft_trip_ids.confirm_trip()

    def action_view_trip(self):
        return {
            'name': "Danh sách chuyến",
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hc.trip',
            'target': 'current',
            'domain': [('id', 'in', self.hc_trip_ids.ids)],
            'context': {'default_source_id': self.id, 'create': 0, 'edit': 0}
        }

    @api.onchange('is_common_info')
    def onchange_is_common_info(self):
        if not self.is_common_info:
            draft_trip_ids = self.hc_trip_ids.filtered(lambda trip: trip.state == 'draft')
            for trip in draft_trip_ids:
                trip.sudo().update({
                    'dealer_id': self.dealer_id,
                    'transport_vendor_id': self.transport_vendor_id,
                    'vehicle_id': self.vehicle_id,
                    'driver_id': self.driver_id
                })

    @api.onchange('transport_vendor_id')
    def onchange_transport_vendor_id(self):
        if not self.is_common_info:
            draft_trip_ids = self.hc_trip_ids.filtered(lambda trip: trip.state == 'draft')
            for trip in draft_trip_ids:
                trip.transport_vendor_id = self.transport_vendor_id

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        if not self.is_common_info:
            draft_trip_ids = self.hc_trip_ids.filtered(lambda trip: trip.state == 'draft')
            for trip in draft_trip_ids:
                trip.vehicle_id = self.vehicle_id

    @api.onchange('driver_id')
    def onchange_driver_id(self):
        if not self.is_common_info:
            draft_trip_ids = self.hc_trip_ids.filtered(lambda trip: trip.state == 'draft')
            for trip in draft_trip_ids:
                trip.driver_id = self.driver_id

    @api.onchange('dealer_id')
    def onchange_dealer_id(self):
        if not self.is_common_info:
            draft_trip_ids = self.hc_trip_ids.filtered(lambda trip: trip.state == 'draft')
            for trip in draft_trip_ids:
                trip.dealer_id = self.dealer_id


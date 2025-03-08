# -*- coding: utf-8 -*-

from odoo import models, fields


class HcVendorReivew(models.Model):
    _name = 'hc.vendor.review'
    _description = 'Đánh giá nhà xe'

    trip_rate = fields.Float(string="Đánh giá chuyến xe")
    cus_rate = fields.Float(string="Đánh giá khách hàng")
    note = fields.Char(string="Ghi chú")
    vendor_id = fields.Many2one('hc.transport.vendor', string="Nhà xe")
    driver_id = fields.Many2one('res.users', string="Tài xế")
    trip_id = fields.Many2one('hc.trip', string="Chuyến")
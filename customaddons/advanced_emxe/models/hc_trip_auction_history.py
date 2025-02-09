# -*- coding: utf-8 -*-

from odoo import models, fields


class HcTripAuctionHistory(models.Model):
    _name = 'hc.trip.auction.history'
    _description = 'Đấu giá chuyến'
    _rec_name = 'transport_vendor_id'

    transport_vendor_id = fields.Many2one('hc.transport.vendor', string="Nhà xe")
    trip_id = fields.Many2one('hc.trip', string="Chuyến")
    est_cost = fields.Float(string="Chi phí bán chuyến")
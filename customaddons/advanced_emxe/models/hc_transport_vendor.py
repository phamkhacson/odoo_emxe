# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class HcTransportVendor(models.Model):
    _name = 'hc.transport.vendor'
    _description = 'Nhà xe'
    _rec_name = 'name'

    name = fields.Char(string="Tên nhà xe")
    phone = fields.Char(string="Điện thoại liên hệ")
    email = fields.Char(string="Email")
    owner_id = fields.Many2one('res.users', string="Chủ nhà xe")
    owner_identification_number = fields.Char(string="Số CMND chủ nhà xe")
    vehicle_ids = fields.One2many('hc.vehicle', 'own_vehicle_id', string="Danh sách xe")
    review_point = fields.Float(string="Điểm đánh giá", compute='_compute_review_point', store=True)
    review_ids = fields.One2many('hc.vendor.review', 'vendor_id', string="Đánh giá")
    bank_account_ids = fields.One2many('hc.bank.account', 'vendor_id', string="Tài khoản ngân hàng")
    is_main_vendor = fields.Boolean(string="Nhà xe chính")

    @api.depends('review_ids', 'review_ids.trip_rate')
    def _compute_review_point(self):
        for rec in self:
            if rec.review_ids:
                rec.review_point = sum(rec.review_ids.mapped('trip_rate')) / len(rec.review_ids)
            else:
                rec.review_point = 0

    def unlink(self):
        for rec in self:
            if rec.id == self.env.ref('advanced_emxe.hc_transport_vendor_hoang_chau').id:
                raise UserError('Không thể xóa nhà xe ' + str(rec.name))
        res = super(HcTransportVendor, self).unlink()
        return res

    @api.constrains('name')
    def _constrain_name(self):
        for rec in self:
            if rec.name:
                exist_record = rec.env['hc.transport.vendor'].sudo().search([('name', '=', rec.name), ('id', '!=', rec.id)])
                if exist_record:
                    raise UserError('Tên của nhà xe đã tồn tại!')

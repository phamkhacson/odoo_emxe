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
    review_point = fields.Float(string="Điểm đánh giá")

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

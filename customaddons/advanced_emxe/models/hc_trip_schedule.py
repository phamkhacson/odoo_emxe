# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class HcTripSchedule(models.Model):
    _name = 'hc.trip.schedule'
    _description = 'Lịch trình chuyến xe'
    _rec_name = 'pick_up_place'

    def _get_start_time_default(self):
        return datetime.now().replace(hour=4, minute=0, second=0) - timedelta(hours=7)

    def _get_end_time_default(self):
        return datetime.now().replace(hour=22, minute=0, second=0) - timedelta(hours=7)

    pick_up_place = fields.Char(string="Điểm đón khách")
    destination = fields.Char(string="Điểm trả khách")
    start_time = fields.Datetime(string="Khởi hành lúc", default=_get_start_time_default)
    end_time = fields.Datetime(string="Kết thúc lúc", default=_get_end_time_default)
    km_estimate = fields.Float(string="KM dự kiến")
    price = fields.Float(string="Đơn giá")
    customer_representative = fields.Char(string="Đại diện KH")
    tour_guide = fields.Char(string="Hướng dẫn viên")
    tour_guide_phone = fields.Char(string="SĐT HDV")
    note = fields.Char(string="Ghi chú")
    preview_id = fields.Many2one('hc.trip.preview')
    trip_id = fields.Many2one('hc.trip', 'Chuyến tương ứng')
    vehicle_count = fields.Integer(string="Số lượng xe", default=1)
    freight_cost = fields.Float(string='Cước vận tải', compute='_compute_freight_cost', store=True)

    @api.model_create_multi
    def create(self, vals):
        res = super(HcTripSchedule, self).create(vals)
        for rec in res:
            if not rec.preview_id.is_common_info:
                rec.sudo().write({
                    'customer_representative': rec.preview_id.customer_representative,
                    'tour_guide': rec.preview_id.tour_guide,
                    'tour_guide_phone': rec.preview_id.tour_guide_phone,
                    'note': rec.preview_id.note
                })
        return res


    @api.depends('price', 'km_estimate')
    def _compute_freight_cost(self):
        for rec in self:
            rec.sudo().freight_cost = rec.price * rec.km_estimate

    def unlink_schedule(self):
        for rec in self:
            if rec.preview_id and rec.preview_id.state == 'confirm':
                if not rec.env.user.has_group('base.group_system'):
                    raise UserError('Chỉ quản trị viên mới có quyền xóa bản ghi ở trạng thái xác nhận!')
            rec.sudo().trip_id.unlink()
            rec.sudo().unlink()

    def action_create_trip(self):
        for rec in self:
            if rec.preview_id and not rec.trip_id:
                operator_id = False
                accountant_id = False
                u_receiver = []
                activity_text = "Điều chuyến cho " + rec.preview_id.hc_code if rec.preview_id.hc_code else "Điều chuyến"
                activity_id = rec.env.ref('mail.mail_activity_data_todo').id
                res_model_id = rec.env['ir.model'].sudo().search([('model', '=', 'hc.trip')], limit=1).id
                if rec.preview_id.dealer_id:
                    executive_group = rec.env['hc.executive.group'].sudo().search([('dealer_id', '=', rec.preview_id.dealer_id.id)], limit=1)
                    if executive_group:
                        if executive_group.operator_id:
                            operator_id = executive_group.operator_id.id
                            u_receiver.append(operator_id)
                        if executive_group.accountant_id:
                            accountant_id = executive_group.accountant_id.id
                            u_receiver.append(accountant_id)
                trip_val = {
                    'hc_code': rec.preview_id.hc_code,
                    'dealer_id': rec.preview_id.dealer_id.id if rec.preview_id.dealer_id else False,
                    'customer_code': rec.preview_id.customer_code,
                    'customer_representative': rec.customer_representative,
                    'end_time': rec.end_time,
                    'tour_guide': rec.tour_guide,
                    'tour_guide_phone': rec.tour_guide_phone,
                    'series_id': rec.preview_id.series_id.id if rec.preview_id.series_id else False,
                    'start_time': rec.start_time,
                    'pick_up_place': rec.pick_up_place,
                    'destination': rec.destination,
                    'note': rec.note,
                    'source_id': rec.preview_id.id,
                    'operator_id': operator_id,
                    'accountant_id': accountant_id,
                    'vehicle_type_id': rec.preview_id.vehicle_type_id.id if rec.preview_id.vehicle_type_id else False,
                }
                new_trip = rec.env['hc.trip'].sudo().create(trip_val)
                rec.sudo().trip_id = new_trip.id
                # cập nhật cước vận tải cho "Tiền thu" của tab "Thu"
                if new_trip.income_detail_ids:
                    freight_cost_line = new_trip.income_detail_ids.filtered(lambda l: l.income_id and l.income_id.is_freight_cost)
                    if freight_cost_line:
                        freight_cost_line[0].price = rec.price
                        freight_cost_line[0].qty = rec.km_estimate
                for u in u_receiver:
                    rec.preview_id._create_trip_activity(activity_id, u, new_trip.id, res_model_id, activity_text)

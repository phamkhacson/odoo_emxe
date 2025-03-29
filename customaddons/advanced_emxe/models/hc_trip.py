# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields, api
from datetime import datetime, timedelta

from odoo.exceptions import UserError

import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(
        dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c
    return round(d, 2)


class HcTrip(models.Model):
    _name = 'hc.trip'
    _description = 'Chuyến xe'
    _rec_name = 'hc_code'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    start_time = fields.Datetime(string="Khởi hành lúc")
    end_time = fields.Datetime(string="Kết thúc lúc")
    note = fields.Char(string="Ghi chú")
    cost_note = fields.Char(string="Ghi chú chi phí")
    auction_ids = fields.One2many('hc.trip.auction.history', 'trip_id', string="Đấu giá")
    auction_count = fields.Integer(string="Số lượng đấu giá", compute="_compute_auction_count", store=True)
    customer_code = fields.Char(string="Mã khách hàng cung cấp")
    hc_code = fields.Char(string="Code HC", copy=False)
    tour_guide = fields.Char(string="Hướng dẫn viên")
    tour_guide_phone = fields.Char(string="SĐT hướng dẫn viên")
    transport_vendor_id = fields.Many2one('hc.transport.vendor', string="Nhà xe")
    vehicle_type_id = fields.Many2one('hc.vehicle.type', string="Loại xe")
    vehicle_id = fields.Many2one('hc.vehicle', string="Xe")
    valid_vehicle_domain = fields.Many2many('hc.vehicle', string="Xe hợp lệ", compute='_compute_valid_vehicle_domain', store=True)
    license_plate = fields.Char(string="Biển kiểm soát", related="vehicle_id.license_plate")
    driver_id = fields.Many2one('res.users', string="Tài xế")
    driver_ids = fields.Many2many('res.users', string="Tài xế", related="vehicle_id.driver_ids")
    driver_phone = fields.Char(string="SĐT tài xế", related="driver_id.phone")
    pick_up_place = fields.Char(string="Điểm đón khách")
    destination = fields.Char(string="Điểm trả khách")
    customer_representative = fields.Char(string="Đại diện khách hàng")
    dealer_id = fields.Many2one('hc.dealer', string="Đại lý")
    series_id = fields.Many2one('hc.trip.series', string="Series chuyến")
    source_id = fields.Many2one('hc.trip.preview', string="Yêu cầu khởi tạo chuyến")
    state = fields.Selection([('draft', 'Khai báo chuyến'), ('waiting', 'Chờ khởi hành'), ('processing', 'Đang thực hiện'), ('payment', 'Chờ chi phí'), ('done', 'Đã hoàn thành'), ('cancel', 'Hủy')], string="Trạng thái", default='draft')
    customer_amount = fields.Float(string="Tiền thu từ khách hàng", compute='compute_amount_data', store=True)
    remain_customer_amount = fields.Float(string="Còn phải thu", compute='compute_amount_data', store=True)
    transport_vendor_amount = fields.Float(string="Doanh thu tính lương", compute='compute_amount_data', store=True)
    cost_payment = fields.Float(string="Đã thanh toán cho nhà xe", compute='compute_amount_data', store=True)
    oil_cost = fields.Float(string="Chi phí dầu")
    other_cost = fields.Float(string="Chi phí khác", compute="compute_hc_cost", store=True)
    hc_income_include_vat = fields.Float(string="Doanh thu bán", compute="compute_hc_income_include_vat", store=True)
    hc_revenue = fields.Float(string="Lợi nhuận gộp", compute='compute_amount_data', store=True)
    net_profit = fields.Float(string="Lợi nhuận ròng", compute='compute_amount_data', store=True)
    operator_id = fields.Many2one('res.users', 'Điều hành')
    accountant_id = fields.Many2one('res.users', 'Kế toán')

    driver_accept = fields.Boolean('Tài xế nhận chuyến?', default=False)
    start_time_actual = fields.Datetime('Thời gian khởi hành thực tế')
    end_time_actual = fields.Datetime('Thời gian kết thúc thực tế')
    trip_pause_time = fields.Datetime('Thời điểm tạm dừng')
    pause_time_count = fields.Integer('Thời gian tạm dừng chuyến')
    total_time_actual = fields.Integer('Thời gian di chuyển thực tế', compute="compute_total_time_actual", store=True)
    distance_actual = fields.Float('Quãng đường thực tế', compute="compute_distance_actual", store=True)
    batch_id = fields.Many2one('hc.trip.batch', 'Chuyến gộp')

    @api.depends('transport_vendor_id')
    def _compute_valid_vehicle_domain(self):
        for rec in self:
            if rec.transport_vendor_id:
                rec.valid_vehicle_domain = rec.transport_vendor_id.vehicle_ids
            else:
                rec.valid_vehicle_domain = self.env['hc.vehicle'].search([])

    @api.depends('locate_list')
    def compute_distance_actual(self):
        for rec in self:
            distance_actual = 0
            if rec.locate_list:
                locate_list = eval(rec.locate_list)
                if len(locate_list) > 1:
                    for i in range(1, len(locate_list)):
                        if not locate_list[i-1]['is_pause']:
                            distance_actual += haversine(locate_list[i-1]['latitude'], locate_list[i-1]['longitude'], locate_list[i]['latitude'], locate_list[i]['longitude'])
            rec.distance_actual = distance_actual

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Không thể xóa chuyến xe có trạng thái khác 'Khai báo chuyến'")
        super(HcTrip, self).unlink()

    @api.depends('start_time_actual', 'end_time_actual', 'pause_time_count')
    def compute_total_time_actual(self):
        for rec in self:
            total_time_actual = 0
            if rec.start_time_actual and rec.end_time_actual:
                total_time_actual = (rec.end_time_actual - rec.start_time_actual).seconds
                if rec.pause_time_count:
                    total_time_actual = total_time_actual - rec.pause_time_count
            rec.total_time_actual = total_time_actual

    @api.depends('income_detail_ids')
    def compute_hc_income_include_vat(self):
        for rec in self:
            hc_income_include_vat = 0
            for line in rec.income_detail_ids:
                income = line.amount
                if line.income_id:
                    vat = round((line.income_id.vat/100) * income, 2)
                    income += vat
                hc_income_include_vat += income
            rec.sudo().hc_income_include_vat = hc_income_include_vat

    @api.depends('operation_cost_ids')
    def compute_hc_cost(self):
        for rec in self:
            other_cost = 0
            for cost in rec.operation_cost_ids:
                other_cost += cost.operation_cost_price
            rec.sudo().other_cost = other_cost

    def _default_income_detail_ids(self):
        income_ids = self.env['hc.trip.entry.config'].sudo().search([('entry_type', 'in', ['income', 'operation_cost'])])
        if income_ids:
            vals = []
            for income in income_ids:
                vals.append({
                    "income_id": income.id,
                    "price": 0,
                    "qty": 0,
                })
            return [(0, 0, e) for e in vals]
        else:
            return False

    def _default_income_payment_detail_ids(self):
        payment_income_ids = self.env['hc.trip.entry.config'].sudo().search([('entry_type', 'in', ['payment_income', 'operation_cost'])])
        if payment_income_ids:
            vals = []
            for payment_income in payment_income_ids:
                vals.append({
                    "payment_income_id": payment_income.id,
                    "payment_amount": 0,
                })
            return [(0, 0, e) for e in vals]
        else:
            return False

    def _default_cost_detail_ids(self):
        cost_ids = self.env['hc.trip.entry.config'].sudo().search([('entry_type', 'in', ['cost', 'operation_cost'])])
        if cost_ids:
            vals = []
            for cost in cost_ids:
                vals.append({
                    "cost_id": cost.id,
                    "price": 0,
                    "qty": 0,
                })
            return [(0, 0, e) for e in vals]
        else:
            return False

    def _default_paid_cost_detail_ids(self):
        paid_cost_ids = self.env['hc.trip.entry.config'].sudo().search([('entry_type', 'in', ['paid_cost', 'operation_cost'])])
        if paid_cost_ids:
            vals = []
            for paid_cost in paid_cost_ids:
                vals.append({
                    "paid_cost_id": paid_cost.id,
                    "payment_amount": 0,
                })
            return [(0, 0, e) for e in vals]
        else:
            return False

    def _default_operation_cost_ids(self):
        operation_cost_ids = self.env['hc.trip.entry.config'].sudo().search([('entry_type', '=', 'operation_cost')])
        if operation_cost_ids:
            vals = []
            for operation_cost in operation_cost_ids:
                vals.append({
                    "operation_cost_id": operation_cost.id,
                    "payment_amount": 0,
                })
            return [(0, 0, e) for e in vals]
        else:
            return False

    def _default_driver_cost_ids(self):
        driver_cost_ids = self.env['hc.trip.entry.config'].sudo().search([('entry_type', 'in', ['operation_cost', 'driver_cost'])])
        if driver_cost_ids:
            vals = []
            for driver_cost in driver_cost_ids:
                vals.append({
                    "driver_cost_id": driver_cost.id,
                    "payment_amount": 0,
                })
            return [(0, 0, e) for e in vals]
        else:
            return False

    income_detail_ids = fields.One2many('hc.trip.amount.detail', 'income_record_id', string="Tiền thu", default=_default_income_detail_ids)
    income_payment_detail_ids = fields.One2many('hc.trip.amount.detail', 'income_payment_record_id', string="Tiền đã thu", default=_default_income_payment_detail_ids)
    cost_detail_ids = fields.One2many('hc.trip.amount.detail', 'cost_record_id', string="Chi phí cho nhà xe", default=_default_cost_detail_ids)
    cost_payment_detail_ids = fields.One2many('hc.trip.amount.detail', 'cost_payment_record_id', string="Tiền đã chi", default=_default_paid_cost_detail_ids)
    operation_cost_ids = fields.One2many('hc.trip.amount.detail', 'operation_cost_record_id', string="Chi phí vận hành nội bộ", default=_default_operation_cost_ids)
    driver_cost_ids = fields.One2many('hc.trip.amount.detail', 'driver_cost_record_id', string="Các khoản lái xe đã chi", default=_default_driver_cost_ids)
    operation_cost_amount = fields.Float(string="Chi phí vận hành nội bộ", compute='compute_amount_data', store=True)
    driver_salary = fields.Float(string="Lương lái xe", compute='compute_amount_data', store=True)
    cost_submited = fields.Boolean(string="Đã gửi duyệt chi", default=False)
    locate_list = fields.Char(string="Danh sách định vị", default="[]")

    @api.depends('operation_cost_ids', 'income_detail_ids', 'income_detail_ids.amount', 'income_payment_detail_ids', 'income_payment_detail_ids.payment_amount', 'cost_detail_ids', 'cost_payment_detail_ids', 'vehicle_type_id', 'vehicle_type_id.driver_salary_percent')
    def compute_amount_data(self):
        for rec in self:
            operation_cost_amount = 0
            operation_cost_amount_exclude_oil = 0
            customer_amount = 0
            customer_payment = 0
            transport_vendor_amount = 0
            cost_payment = 0
            commission_fee = 0
            for oc in rec.operation_cost_ids:
                operation_cost_amount += oc.operation_cost_price
                operation_cost_amount_exclude_oil += oc.operation_cost_price
                if oc.operation_cost_id and oc.operation_cost_id.name == 'COM':
                    commission_fee += oc.operation_cost_price
            for income in rec.income_detail_ids:
                customer_amount += income.amount
            for payment in rec.income_payment_detail_ids:
                customer_payment += payment.payment_amount
            for cost in rec.cost_detail_ids:
                transport_vendor_amount += cost.amount
            for cost_p in rec.cost_payment_detail_ids:
                cost_payment += cost_p.payment_amount
            driver_salary_percent = 0
            if rec.vehicle_type_id:
                driver_salary_percent = rec.vehicle_type_id.driver_salary_percent
            rec.sudo().operation_cost_amount = operation_cost_amount
            rec.sudo().customer_amount = customer_amount
            rec.sudo().remain_customer_amount = customer_amount - customer_payment
            rec.sudo().cost_payment = cost_payment
            rec.sudo().transport_vendor_amount = transport_vendor_amount
            rec.sudo().hc_revenue = customer_amount - transport_vendor_amount
            rec.sudo().net_profit = customer_amount - transport_vendor_amount - commission_fee
            rec.sudo().driver_salary = (transport_vendor_amount - operation_cost_amount_exclude_oil) * driver_salary_percent/100

    @api.depends('auction_ids')
    def _compute_auction_count(self):
        for rec in self:
            rec.sudo().auction_count = len(rec.auction_ids)

    def confirm_trip(self):
        for rec in self:
            if not rec.transport_vendor_id:
                raise UserError('Thiếu cấu hình Nhà xe.')
            if not rec.vehicle_id:
                raise UserError('Thiếu cấu hình Xe.')
            if not rec.driver_id:
                raise UserError('Thiếu cấu hình Tài xế.')
            rec.sudo().state = 'waiting'
            # gửi noti cho lái xe
            if rec.driver_id:
                hc_code = rec.hc_code if rec.hc_code else ''
                pick_up_place = rec.pick_up_place if rec.pick_up_place else ''
                destination = rec.destination if rec.destination else ''
                start_time = rec.start_time.strftime("%d/%m/%Y %H:%M:%S") if rec.start_time else ''
                end_time = rec.end_time.strftime("%d/%m/%Y %H:%M:%S") if rec.end_time else ''
                vehicle_type_id = rec.vehicle_type_id.name if rec.vehicle_type_id else ''
                transport_vendor_id = rec.transport_vendor_id.name if rec.transport_vendor_id else ''
                license_plate = rec.vehicle_id.license_plate if rec.vehicle_id else ''
                tour_guide = rec.tour_guide if rec.tour_guide else ''
                tour_guide_phone = rec.tour_guide_phone if rec.tour_guide_phone else ''
                note = rec.note if rec.note else ''
                message = ('Bạn được phân công chuyến với mã: ' + hc_code + ' <br>' +
                           'Điểm đón khách: ' + pick_up_place + ' <br>' +
                           'Điểm trả khách: ' + destination + ' <br>' +
                           'Khởi hành: ' + start_time + ' <br>' +
                           'Kết thúc: ' + end_time + ' <br>' +
                           'Loại xe: ' + vehicle_type_id + ' <br>' +
                           'Nhà xe: ' + transport_vendor_id + ' <br>' +
                           'Xe: ' + license_plate + ' <br>' +
                           'Tài xế: ' + rec.driver_id.name + ' <br>' +
                           'Hướng dẫn viên: ' + tour_guide + ' <br>' +
                           'SĐT hướng dẫn viên: ' + tour_guide_phone + ' <br>' +
                           'Ghi chú: ' + note
                           )
                rec.message_post(body=message, message_type='notification', partner_ids=[rec.driver_id.partner_id.id])

                data = {
                    'record_id': str(rec.id),
                    'type': 'dieu_chuyen'
                }
                notification = {
                    'title': 'Bạn vừa được phân giao chuyến đi',
                    'body': f'Bạn vừa được Quản trị viên phân giao chuyến đi {pick_up_place} - {destination} vào {rec.start_time.strftime("%d/%m/%Y %H:%M:%S")}. Click chấp nhận để nhận chuyến đi'
                }
                self.env['emxe.firebase.config'].sudo().send_fcm_notification(data=data, notification=notification, user_id=rec.driver_id)

    def mark_as_processing(self):
        for rec in self:
            existed_processing_trip = self.env['hc.trip'].sudo().search([('driver_id', '=', rec.driver_id.id), ('state', '=', 'processing')])
            if existed_processing_trip:
                raise UserError('Tài xế đang thực hiện chuyến khác.')
            rec.sudo().state = 'processing'

    def mark_as_payment(self):
        for rec in self:
            rec.sudo().state = 'payment'
            pick_up_place = rec.pick_up_place if rec.pick_up_place else ''
            destination = rec.destination if rec.destination else ''

            message = (f'Chuyến đi {pick_up_place} - {destination} của bạn đã được hoàn thành. Vào trang báo cáo để hoàn thiện chi phí chuyến đi.')
            rec.message_post(body=message, message_type='notification', partner_ids=[rec.driver_id.partner_id.id])
            data = {
                'record_id': str(rec.id),
                'type': 'noti'
            }
            notification = {
                'title': 'Chuyến đi đã hoàn thành',
                'body': f'Chuyến đi {pick_up_place} - {destination} của bạn đã được hoàn thành. Vào trang báo cáo để hoàn thiện chi phí chuyến đi.'
            }
            self.env['emxe.firebase.config'].sudo().send_fcm_notification(data=data, notification=notification,
                                                                          user_id=rec.driver_id)


    def mark_as_done(self):
        for rec in self:
            rec.sudo().state = 'done'
            pick_up_place = rec.pick_up_place if rec.pick_up_place else ''
            destination = rec.destination if rec.destination else ''
            message = (
                f'Chuyến đi {pick_up_place} - {destination} của bạn đã được thanh toán. Xem chi tiết ở trang cá nhân')
            rec.message_post(body=message, message_type='notification', partner_ids=[rec.driver_id.partner_id.id])
            data = {
                'record_id': str(rec.id),
                'type': 'noti'
            }
            notification = {
                'title': 'Chuyến đi đã được thanh toán',
                'body': f'Chuyến đi {pick_up_place} - {destination} của bạn đã được thanh toán. Xem chi tiết ở trang cá nhân'
            }
            self.env['emxe.firebase.config'].sudo().send_fcm_notification(data=data, notification=notification,
                                                                          user_id=rec.driver_id)

    def action_cancel_trip(self):
        for rec in self:
            rec.sudo().state = 'cancel'

    def action_draft_trip(self):
        for rec in self:
            rec.sudo().write({
                'state': 'draft',
                'driver_accept': False
            })

    def send_notify_to_dealer(self):
        mail_template = self.env.ref('advanced_emxe.hc_mail_template_create_trip')
        for rec in self:
            if rec.dealer_id:
                if rec.dealer_id.email:
                    email_values = {'email_to': rec.dealer_id.email}
                    mail_template.sudo().send_mail(rec.id, force_send=True, raise_exception=True, email_values=email_values)
                # gửi thông báo trên hệ thống cho đại lý
                if rec.dealer_id.related_user_ids:
                    hc_code = rec.hc_code if rec.hc_code else ''
                    pick_up_place = rec.pick_up_place if rec.pick_up_place else ''
                    message = 'Chuyến xe với mã: ' + hc_code + ', điểm đón khách: ' + pick_up_place + ' đã được xác nhận.'
                    rec.message_post(body=message, message_type='notification', partner_ids=rec.dealer_id.related_user_ids.partner_id.ids)

    def action_view_auction(self):
        return {
            'name': "Đấu giá chuyến",
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hc.trip.auction.history',
            'target': 'current',
            'domain': [('trip_id', '=', self.id)],
            'context': {'default_trip_id': self.id}
        }

    def action_view_trip(self):
        return {
            'name': "Chuyến xe",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hc.trip',
            'target': 'current',
            'res_id': self.id,
            'context': {'default_source_id': self.id}
        }

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(HcTrip, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        if 'customer_amount' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    total_customer_amount = 0.0
                    for record in lines:
                        total_customer_amount += record.customer_amount
                    line['customer_amount'] = total_customer_amount
        if 'transport_vendor_amount' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    total_transport_vendor_amount = 0.0
                    for record in lines:
                        total_transport_vendor_amount += record.transport_vendor_amount
                    line['transport_vendor_amount'] = total_transport_vendor_amount
        if 'hc_revenue' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    total_hc_revenue = 0.0
                    for record in lines:
                        total_hc_revenue += record.hc_revenue
                    line['hc_revenue'] = total_hc_revenue
        if 'hc_income_include_vat' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    total_hc_income_include_vat = 0.0
                    for record in lines:
                        total_hc_income_include_vat += record.hc_income_include_vat
                    line['hc_income_include_vat'] = total_hc_income_include_vat
        if 'driver_salary' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    total_driver_salary = 0.0
                    for record in lines:
                        total_driver_salary += record.driver_salary
                    line['driver_salary'] = total_driver_salary
        if 'other_cost' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    total_other_cost = 0.0
                    for record in lines:
                        total_other_cost += record.other_cost
                    line['other_cost'] = total_other_cost
        return res

    @api.onchange('transport_vendor_id')
    def _onchange_transport_vendor_id(self):
        if self.transport_vendor_id:
            self.vehicle_id = self.transport_vendor_id.vehicle_ids[0].id if self.transport_vendor_id.vehicle_ids else False
            # if self.env.user.has_group('advanced_emxe.hc_group_operator') and self.env.user.transport_vendor_id and self.env.user.transport_vendor_id.id == self.env.ref('advanced_emxe.hc_transport_vendor_hoang_chau').id:
            #     return {'domain': {'vehicle_id': [('id', '!=', False)]}}
            # else:
            #     return {'domain': {'vehicle_id': [('own_vehicle_id', '=', self.transport_vendor_id.id)]}}

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            if not self.transport_vendor_id:
                self.transport_vendor_id = self.own_vehicle_id
            if self.vehicle_id.driver_ids:
                self.driver_id = self.vehicle_id.driver_ids[0].id
            else:
                self.driver_id = False
        else:
            self.driver_id = False


    def cron_trip_start_noti(self):
        now = datetime.now()
        time = datetime.now() + timedelta(hours=1)
        trip_ids = self.env['hc.trip'].sudo().search([('state', '=', 'waiting'), ('start_time', '>', now), ('start_time', '<=', time)])
        for trip in trip_ids:
            pick_up_place = trip.pick_up_place if trip.pick_up_place else ''
            destination = trip.destination if trip.destination else ''
            data = {
                'record_id': str(trip.id),
                'type': 'sap_khoi_hanh'
            }
            notification = {
                'title': 'Chuyến đi sắp tới',
                'body': f'Chuyến đi sắp khởi hành từ {pick_up_place} - {destination} vào lúc {trip.start_time.strftime("%d/%m/%Y %H:%M:%S")}.'
            }
            self.env['emxe.firebase.config'].sudo().send_fcm_notification(data=data, notification=notification,
                                                                          user_id=trip.driver_id)
from odoo import fields, models, api
from odoo.exceptions import UserError


class wizardChangeDriver(models.TransientModel):
    _name = 'wizard.change.driver'

    trip_id = fields.Many2one('hc.trip', string="Chuyến")
    transport_vendor_id = fields.Many2one('hc.transport.vendor', string="Nhà xe")
    vehicle_id = fields.Many2one('hc.vehicle', string="Xe")
    valid_vehicle_domain = fields.Many2many('hc.vehicle', string="Xe hợp lệ", compute='_compute_valid_vehicle_domain', store=True)
    driver_id = fields.Many2one('res.users', string="Tài xế")
    driver_ids = fields.Many2many('res.users', string="Tài xế", related="vehicle_id.driver_ids")

    @api.depends('transport_vendor_id')
    def _compute_valid_vehicle_domain(self):
        for rec in self:
            if rec.transport_vendor_id:
                rec.valid_vehicle_domain = rec.transport_vendor_id.vehicle_ids
            else:
                rec.valid_vehicle_domain = self.env['hc.vehicle'].search([])

    @api.onchange('transport_vendor_id')
    def _onchange_transport_vendor_id(self):
        if self.transport_vendor_id:
            self.vehicle_id = self.transport_vendor_id.vehicle_ids[
                0].id if self.transport_vendor_id.vehicle_ids else False

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            if not self.transport_vendor_id:
                self.transport_vendor_id = self.vehicle_id.own_vehicle_id
            if self.vehicle_id.driver_ids:
                self.driver_id = self.vehicle_id.driver_ids[0].id
            else:
                self.driver_id = False
        else:
            self.driver_id = False

    def confirm(self):
        if self.trip_id.driver_id != self.driver_id:
            rec = self.trip_id
            if rec.driver_id:
                self.trip_id.message_post(
                    body='Tài xế ' + rec.driver_id.name + ' đã bị thay thế bởi ' + self.driver_id.name,
                    message_type='notification',
                    partner_ids=[rec.driver_id.partner_id.id]
                )
                data = {
                    'record_id': str(rec.id),
                    'type': 'dieu_chuyen'
                }
                notification = {
                    'title': 'Thay đổi tài xế',
                    'body': f'Chuyến xe {rec.hc_code} đã được điều sang tài xế khác.'
                }
                self.env['emxe.firebase.config'].sudo().send_fcm_notification(data=data, notification=notification,
                                                                              user_id=rec.driver_id)
            self.trip_id.sudo().write({
                'transport_vendor_id': self.transport_vendor_id.id,
                'vehicle_id': self.vehicle_id.id,
                'driver_id': self.driver_id.id,
            })
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
                    'body': f'Bạn vừa được Quản trị viên phân giao chuyến đi {pick_up_place} - {destination} vào {start_time}. Click chấp nhận để nhận chuyến đi'
                }
                self.env['emxe.firebase.config'].sudo().send_fcm_notification(data=data, notification=notification,
                                                                              user_id=rec.driver_id)
        return {'type': 'ir.actions.act_window_close'}

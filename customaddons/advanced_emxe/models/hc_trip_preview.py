from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class HcTripPreview(models.Model):
    _name = 'hc.trip.preview'
    _description = 'Khởi tạo chuyến xe'
    _rec_name = 'hc_code'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_default_hc_code(self):
        current_year = str(datetime.now().year)
        current_month = str(datetime.now().month)
        if len(current_month) == 1:
            current_month = '0' + current_month
        current_date = str(datetime.now().day)
        if len(current_date) == 1:
            current_date = '0' + current_date
        current_hour = str((datetime.now() + timedelta(hours=7)).hour)
        if len(current_hour) == 1:
            current_hour = '0' + current_hour
        current_min = str(datetime.now().minute)
        if len(current_min) == 1:
            current_min = '0' + current_min
        hc_code = 'HC' + current_year + current_month + current_date + current_hour + current_min
        return hc_code

    customer_code = fields.Char(string="Mã khách hàng cung cấp")
    hc_code = fields.Char(string="Code HC", copy=False, default=_get_default_hc_code)
    vehicle_type_id = fields.Many2one('hc.vehicle.type', string="Loại xe")
    dealer_id = fields.Many2one('hc.dealer', string="Đại lý")
    series_id = fields.Many2one('hc.trip.series', string="Series chuyến")
    schedule_ids = fields.One2many('hc.trip.schedule', 'preview_id', string='Lịch trình')
    trip_ids = fields.One2many('hc.trip', 'source_id', string='Chuyến')
    state = fields.Selection([('draft', 'Nháp'), ('confirm', 'Xác nhận')], string="Trạng thái", default='draft')
    pick_up_place = fields.Char(string="Điểm đón khách", compute='_compute_pick_up_place', store=True)
    is_common_info = fields.Boolean(string="Chỉnh sửa chi tiết", default=False)
    customer_representative = fields.Char(string="Đại diện KH")
    tour_guide = fields.Char(string="Hướng dẫn viên")
    tour_guide_phone = fields.Char(string="SĐT HDV")
    note = fields.Char(string="Ghi chú")
    hc_trip_batch_id = fields.Many2one('hc.trip.batch', "Chuyến xe gộp")

    @api.onchange('is_common_info')
    def onchange_is_common_info(self):
        if not self.is_common_info:
            for schedule in self.schedule_ids:
                schedule.sudo().write({
                    'customer_representative': self.customer_representative,
                    'tour_guide': self.tour_guide,
                    'tour_guide_phone': self.tour_guide_phone,
                    'note': self.note
                })

    @api.onchange('customer_representative')
    def onchange_customer_representative(self):
        if not self.is_common_info:
            for schedule in self.schedule_ids:
                schedule.customer_representative = self.customer_representative

    @api.onchange('tour_guide')
    def onchange_tour_guide(self):
        if not self.is_common_info:
            for schedule in self.schedule_ids:
                schedule.tour_guide = self.tour_guide

    @api.onchange('tour_guide_phone')
    def onchange_tour_guide_phone(self):
        if not self.is_common_info:
            for schedule in self.schedule_ids:
                schedule.tour_guide_phone = self.tour_guide_phone

    @api.onchange('note')
    def onchange_note(self):
        if not self.is_common_info:
            for schedule in self.schedule_ids:
                schedule.note = self.note

    @api.depends('schedule_ids', 'schedule_ids.pick_up_place')
    def _compute_pick_up_place(self):
        for rec in self:
            pick_up_place = []
            for line in rec.schedule_ids:
                if line.pick_up_place:
                    pick_up_place.append(line.pick_up_place)
            rec.sudo().pick_up_place = ', '.join(pick_up_place)

    def action_view_trip(self):
        return {
            'name': "Danh sách chuyến",
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hc.trip',
            'target': 'current',
            'domain': [('id', 'in', self.trip_ids.ids)],
            'context': {'default_source_id': self.id, 'create': 0, 'edit': 0}
        }

    def action_view_batch_trip(self):
        if not self.hc_trip_batch_id:
            raise UserError('Không có chuyến gộp')
        return {
            'name': "Chuyến gộp",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hc.trip.batch',
            'res_id': self.hc_trip_batch_id.id,
            'target': 'current',
            'context': {'create': 0, 'delete': 0}
        }

    def confirm(self):
        for rec in self:
            # if not rec.is_common_info:
            #     if not rec.customer_representative:
            #         raise UserError("Thiếu cấu hình Đại diện khách hàng")
            #     if not rec.tour_guide:
            #         raise UserError("Thiếu cấu hình Hướng dẫn viên")
            #     if not rec.tour_guide_phone:
            #         raise UserError("Thiếu cấu hình Sđt Hướng dẫn viên")
            #     if not rec.note:
            #         raise UserError("Thiếu cấu hình Ghi chú")
            rec.sudo().state = 'confirm'
            operator_id = False
            accountant_id = False
            u_receiver = []
            activity_text = "Điều chuyến cho " + rec.hc_code if rec.hc_code else "Điều chuyến"
            activity_id = self.env.ref('mail.mail_activity_data_todo').id
            res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'hc.trip')], limit=1).id
            if rec.dealer_id:
                executive_group = rec.env['hc.executive.group'].sudo().search([('dealer_id', '=', rec.dealer_id.id)], limit=1)
                if executive_group:
                    if executive_group.operator_id:
                        operator_id = executive_group.operator_id.id
                        u_receiver.append(operator_id)
                    if executive_group.accountant_id:
                        accountant_id = executive_group.accountant_id.id
                        u_receiver.append(accountant_id)
            if rec.schedule_ids:
                batch_trip_id = rec.env['hc.trip.batch'].sudo().create({
                    'hc_code': rec.hc_code,
                })
                rec.hc_trip_batch_id = batch_trip_id
                for schedule in rec.schedule_ids:
                    trip_val = {
                        'hc_code': rec.hc_code,
                        'batch_id': batch_trip_id.id,
                        'dealer_id': rec.dealer_id.id if rec.dealer_id else False,
                        'customer_code': rec.customer_code,
                        'customer_representative': schedule.customer_representative,
                        'tour_guide': schedule.tour_guide,
                        'end_time': schedule.end_time,
                        'tour_guide_phone': schedule.tour_guide_phone,
                        'series_id': rec.series_id.id if rec.series_id else False,
                        'start_time': schedule.start_time,
                        'pick_up_place': schedule.pick_up_place,
                        'destination': schedule.destination,
                        'note': schedule.note,
                        'source_id': rec.id,
                        'operator_id': operator_id,
                        'accountant_id': accountant_id,
                        'vehicle_type_id': rec.vehicle_type_id.id if rec.vehicle_type_id else False,
                    }
                    if schedule.vehicle_count > 1:
                        for i in range(0, schedule.vehicle_count):
                            new_trip = rec.env['hc.trip'].sudo().create(trip_val)
                            for u in u_receiver:
                                rec._create_trip_activity(activity_id, u, new_trip.id, res_model_id, activity_text)
                    else:
                        new_trip = rec.env['hc.trip'].sudo().create(trip_val)
                        schedule.sudo().trip_id = new_trip.id
                        #cập nhật cước vận tải cho "Tiền thu" của tab "Thu"
                        if new_trip.income_detail_ids:
                            freight_cost_line = new_trip.income_detail_ids.filtered(lambda l: l.income_id and l.income_id.is_freight_cost)
                            if freight_cost_line:
                                freight_cost_line[0].price = schedule.price
                                freight_cost_line[0].qty = schedule.km_estimate
                        for u in u_receiver:
                            rec._create_trip_activity(activity_id, u, new_trip.id, res_model_id, activity_text)

    def _create_trip_activity(self, activity_type_id, user_id, res_id, res_model_id, summary):
        self.env['mail.activity'].sudo().create({
            'activity_type_id': activity_type_id,
            'user_id': user_id,
            'res_id': res_id,
            'res_model_id': res_model_id,
            'summary': summary,
        })

    def select_series(self):
        view_id = self.env.ref('advanced_emxe.wizard_select_trip_data_view_form').id
        return {
            'name': 'Chọn series chuyến',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'wizard.select.trip.data',
            'view_id': view_id,
            'target': 'new',
            'context': {'default_preview_id': self.id, 'default_type': 'series'},
        }

    def select_stage(self):
        view_id = self.env.ref('advanced_emxe.wizard_select_trip_data_view_form').id
        return {
            'name': 'Chọn chặng',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'wizard.select.trip.data',
            'view_id': view_id,
            'target': 'new',
            'context': {'default_preview_id': self.id, 'default_type': 'stage'},
        }

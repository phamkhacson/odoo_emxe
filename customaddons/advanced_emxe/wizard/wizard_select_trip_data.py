from odoo import fields, models
from odoo.exceptions import UserError


class WizardSelectTripData(models.TransientModel):
    _name = 'wizard.select.trip.data'

    stage_ids = fields.Many2many('hc.trip.stage', string="Chặng")
    series_id = fields.Many2one('hc.trip.series', string="Chuyến")
    preview_id = fields.Many2one('hc.trip.preview', string="Yêu cầu tạo chuyến")
    type = fields.Selection([('stage', 'Chọn chặng'), ('series', 'Chọn chuyến')], string="Loại")

    def confirm(self):
        if self.preview_id:
            if self.type == 'stage':
                if self.stage_ids:
                    schedule_vals = []
                    for stage in self.stage_ids:
                        schedule_vals.append({
                            'pick_up_place': stage.pick_up_place,
                            'destination': stage.destination,
                            'km_estimate': stage.km_count,
                            'note': stage.note,
                        })
                    if len(schedule_vals) > 0:
                        self.preview_id.sudo().schedule_ids = [(0, 0, val) for val in schedule_vals]
                else:
                    raise UserError('Chưa chọn chặng!')
            elif self.type == 'series':
                if self.series_id:
                    if self.series_id.trip_stage_ids:
                        schedule_vals = []
                        for stage in self.series_id.trip_stage_ids:
                            schedule_vals.append({
                                'pick_up_place': stage.pick_up_place,
                                'destination': stage.destination,
                                'km_estimate': stage.km_count,
                                'note': stage.note,
                            })
                        if len(schedule_vals) > 0:
                            self.preview_id.sudo().schedule_ids = [(5, 0, 0)] + [(0, 0, val) for val in schedule_vals]
                    self.preview_id.sudo().series_id = self.series_id.id
                else:
                    raise UserError('Chưa chọn chuyến!')
            else:
                pass

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    dealer_id = fields.Many2one('hc.dealer', string='Đại lý liên kết')
    vehicle_id = fields.Many2one('hc.vehicle', string='Xe quản lý')
    vehicle_ids = fields.Many2many('hc.vehicle', string='Xe quản lý')
    transport_vendor_id = fields.Many2one('hc.transport.vendor', string='Nhà xe liên kết')
    identification_number = fields.Char(string="Số CMND/CCCD")
    position = fields.Char(string="Chức vụ")
    emxe_gender = fields.Selection([
        ('male', 'Nam'), ('female', 'Nữ')], index=True,
        default='male', string='Giới tính')

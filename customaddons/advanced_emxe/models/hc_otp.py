# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

import random
import string

class HcOTP(models.Model):
    _name = 'hc.otp'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user = fields.Char(string="User")
    otp = fields.Char(string="OTP")
    expired = fields.Datetime(string="Expired")
    state = fields.Selection([
        ('new', 'New'),
        ('used', 'Used')
    ], string="State", default='new')

    def generate_otp(self, user):
        # generate a random 6-digit OTP expired in 5 minutes

        otp = ''.join(random.choices(string.digits, k=6))
        expired = datetime.now() + timedelta(minutes=5)
        res = self.create({
            'user': user,
            'otp': otp,
            'expired': expired
        })
        return res

    def send_notify_to_user(self):
        mail_template = self.env.ref('advanced_emxe.hc_mail_send_otp')
        for rec in self:
            if '@gmail.com' in rec.user:
                email_values = {'email_to': rec.user}
                mail_template.sudo().send_mail(rec.id, force_send=True, raise_exception=True, email_values=email_values)



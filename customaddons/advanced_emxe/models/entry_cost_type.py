# -*- coding: utf-8 -*-

from odoo import models, fields


class entryCostType(models.Model):
    _name = 'entry.cost.type'
    _rec_name = 'name'

    name = fields.Char(string="Tên")
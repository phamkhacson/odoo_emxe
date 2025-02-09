from odoo import fields, models, api


class EMXEFlutterLog(models.Model):
    _name = 'emxe.flutter.log'
    _order = 'id desc'


    name = fields.Char()
    type = fields.Char()
    description = fields.Text()

    def _create_flutter_log(self, name=None, type=None, description=None):
        """
        Logging for api
        param
        type: [request, response, error].
        """
        self['emxe.flutter.log'].sudo().create({
            'name': name,
            'type': type,
            'description': description,
        })
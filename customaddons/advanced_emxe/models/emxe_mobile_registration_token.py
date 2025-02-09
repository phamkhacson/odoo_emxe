from odoo import fields, models, api
import json

try:
    import firebase_admin
    from firebase_admin import messaging
    from firebase_admin import credentials
except ImportError:
    firebase_admin = None

try:
    from google.oauth2 import service_account
    from google.auth.transport import requests as google_requests
except ImportError:
    service_account = None
import base64
import json
import requests


class EMXEMobileRegistrationToken(models.Model):
    _name = 'emxe.mobile.registration.token'
    _description = 'Description'
    _rec_name = 'user_id'

    token = fields.Char()
    user_id = fields.Many2one('res.users', 'User')
    test_noti_id = fields.Many2one('mail.notification', 'Test noti')

    def test_send_fcm_notification(self):
        firebase_app = self.env['emxe.firebase.config'].sudo().search([], limit=1)
        if len(firebase_app) > 0:
            firebase_data = json.loads(
                base64.b64decode(firebase_app.firebase_admin_key_file).decode())
            ## todo check validate các biến tokens, data, notification
            firebase_credentials = service_account.Credentials.from_service_account_info(
                firebase_data,
                scopes=['https://www.googleapis.com/auth/firebase.messaging']
            )
            firebase_credentials.refresh(google_requests.Request())
            auth_token = firebase_credentials.token
            #     ## todo bắt những registration nào bị lỗi thì xóa khỏi hệ thống ( do không bắt được lỗi uninstall app )
            noti_id = self.env['mail.notification'].sudo().search([('res_partner_id', '=', self.user_id.partner_id.id), ('is_read', '!=', True)], limit=1)
            self.test_noti_id = noti_id
            res = requests.post(
                f'https://fcm.googleapis.com/v1/projects/{firebase_data["project_id"]}/messages:send',
                json={
                    'message': {
                        "notification": {
                            "body": "emxe Test Body",
                            "title": "emxe Test Title"
                        },
                        'data': {
                            'noti_type': 'approval',
                            # 'noti_type': 'timeoff',
                            'record_id': str(noti_id.id) if noti_id else None
                        },
                        'token': self.token
                    }
                },
                headers={'authorization': f'Bearer {auth_token}'},
                timeout=5
            )
            print(res.text)
            return

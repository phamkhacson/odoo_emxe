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


class EMXEFirebaseConfig(models.Model):
    _name = 'emxe.firebase.config'

    name = fields.Char(default="Firebase Project")
    firebase_admin_key_file = fields.Binary('Firebase Admin Key File')

    def emxe_firebase_config_views(self):
        rec = self.env['emxe.firebase.config'].sudo().search([], limit=1)
        form_view = self.env.ref('advanced_emxe.emxe_firebase_config_form_view',
                                 raise_if_not_found=False)
        if rec:
            rec_id = rec.id
        else:
            new_obj = self.env['emxe.firebase.config'].sudo().create({
                'name': 'Firebase Project'
            })
            rec_id = new_obj.id
        return {
            'name': 'Firebase Project',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'current',
            'views': [(form_view.id, 'form')],
            'res_id': rec_id,
            'res_model': 'emxe.firebase.config'
        }

    @api.model
    def send_fcm_notification(self, data=False, notification=False, user_id=False):
        #todo data phai la string
        if user_id and data and notification:
            tokens = self.env['emxe.mobile.registration.token'].sudo().search([('user_id', '=', user_id.id)])
            # data = {
            #     'noti_type': 'approval',
            #     # 'noti_type': 'timeoff',
            #     'record_id': '3'
            # }
            # notification = {
            #                 "body": "emxe Body",
            #                 "title": "emxe TITLE"
            #             }
            try:
                firebase_app = self.env['emxe.firebase.config'].sudo().search([], limit=1)
                firebase_data = json.loads(
                    base64.b64decode(firebase_app.firebase_admin_key_file).decode())
                ## todo check validate các biến tokens, data, notification
                firebase_credentials = service_account.Credentials.from_service_account_info(
                    firebase_data,
                    scopes=['https://www.googleapis.com/auth/firebase.messaging']
                )
                firebase_credentials.refresh(google_requests.Request())
                auth_token = firebase_credentials.token
            except Exception as e:
                print(str(e))
                pass
            # todo bắt những registration nào bị lỗi thì xóa khỏi hệ thống (tính trường hợp uninstall app ).
            for token in tokens:
                try:
                    res = requests.post(
                        f'https://fcm.googleapis.com/v1/projects/{firebase_data["project_id"]}/messages:send',
                        json={
                            'message': {
                                "notification": notification,
                                'data': data,
                                'token': token.token }
                        },
                        headers={'authorization': f'Bearer {auth_token}'},
                        timeout=5
                    )
                    # xóa bản ghi token nếu token không khả dụng ( đề phòng trường hợp người dùng gỡ app )
                    result = res.json()
                    if 'error' in result:
                        if 'message' in result['error']:
                            if result['error']['message'] == 'The registration token is not a valid FCM registration token':
                                self.sudo().unlink()
                    print(res.json())
                except Exception as e:
                    print(str(e))
                    pass
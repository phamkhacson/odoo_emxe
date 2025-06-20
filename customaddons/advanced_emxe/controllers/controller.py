# -*- coding: utf-8 -*-
from odoo import http
from odoo import fields, models, api
from odoo.http import request, _logger
from datetime import datetime, timedelta
import logging
import math
import requests
import re
from haversine import haversine, Unit

def calculate_distance(lat1, lon1, lat2, lon2):
    # Define the two points as tuples
    point1 = (lat1, lon1)
    point2 = (lat2, lon2)

    # Calculate the distance in kilometers
    distance = haversine(point1, point2, unit=Unit.KILOMETERS)
    return round(distance, 2)


def _create_flutter_log(env, name=None, type=None, description=None):
    """
    Logging for api
    param
    type: [request, response, error].
    """
    env['emxe.flutter.log'].sudo().create({
        'name': name,
        'type': type,
        'description': description,
    })


def strip_html_tags(html):
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', html)
    text.replace('\n', '')
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text

# function to calculate distance by real road map with google api
def get_distance(lat1, lon1, lat2, lon2):
    try:
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&origins={lat1},{lon1}&destinations={lat2},{lon2}&key=AIzaSyDJbwAif54Z_iKJwyo5hzBUbWbIo0n-Na0"
        response = requests.get(url)
        data = response.json()
        distance = data['rows'][0]['elements'][0]['distance']['value']
        return distance
    except Exception as e:
        return 0


class EMXEFlutterApi(http.Controller):

    @http.route('/emxe_api/send_otp', type='json', auth="none")
    def send_otp(self, **kw):
        try:
            user = kw.get('user')
            if not user:
                return {
                    'status': 'fail',
                    'code': 400,
                    'message': 'Thiếu user'
                }
            type = kw.get('type')
            if not type:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu type",
                    "data": {
                        "success": False
                    }
                }
            if type == 'gmail':
                if '@gmail.com' in user:
                    otp = request.env['hc.otp'].sudo().generate_otp(user)
                    otp.send_notify_to_user()
                    return {
                        "status": "success",
                        "code": 200,
                        "message": "Gửi thành công",
                        "data": {
                            "success": True
                        }
                    }
                else:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "User không phải là email",
                        "data": {
                            "success": False
                        }
                    }
            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "User không phải là email",
                    "data": {
                        "success": False
                    }
                }
        except Exception as e:
            return {
                "status": "fail",
                "code": 400,
                "message": e,
                "data": {
                    "success": False
                }
            }

    # api submit otp
    @http.route('/emxe_api/submit_otp', type='json', auth="none")
    def submit_otp(self, **kw):
        try:
            user = kw.get('user')
            if not user:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu user",
                    "data": {
                        "success": False
                    }
                }
            otp = kw.get('otp')
            if not otp:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu OTP",
                    "data": {
                        "success": False
                    }
                }
            otp_id = request.env['hc.otp'].sudo().search([('user', '=', user), ('otp', '=', otp)])
            if otp_id:
                if otp_id.expired < datetime.now():
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "OTP hết hạn",
                        "data": {
                            "success": False
                        }
                    }
                else:
                    if otp_id.state == 'new':
                        otp_id.state = 'used'
                        return {
                            "status": "success",
                            "code": 200,
                            "message": "OTP chính xác",
                            "data": {
                                "success": True
                            }
                        }
                    else:
                        return {
                            "status": "fail",
                            "code": 400,
                            "message": "OTP đã được sử dụng",
                            "data": {
                                "success": False
                            }
                        }
            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "OTP không chính xác",
                    "data": {
                        "success": False
                    }
                }
        except Exception as e:
            return {
                "status": "fail",
                "code": 400,
                "message": e,
                "data": {
                    "success": False
                }
            }

    @http.route('/emxe_api/get_phone_email', type='json', auth="none")
    def get_phone_email(self, **kw):
        try:
            user = kw.get('user')
            if not user:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu user",
                    "data": {
                        "success": False
                    }
                }
            if '@gmail.com' in user:
                odoo_user = request.env['res.users'].sudo().search([('login', '=', user)], limit=1)
            else:
                odoo_user = request.env['res.users'].sudo().search([('phone', '=', user)], limit=1)
            if odoo_user:
                return {
                    "status": "success",
                    "code": 200,
                    "message": "success",
                    "data": {
                        "email": odoo_user.login,
                        "phone": odoo_user.phone,
                    }
                }
            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thông tin không hợp lệ",
                    "data": {
                        "success": False
                    }
                }
        except Exception as e:
            return {
                "status": "fail",
                "code": 400,
                "message": e,
                "data": {
                    "success": False
                }
            }

    @http.route('/emxe_api/get_employee_profile', auth='user', csrf=False, type='json')
    def get_employee_profile(self, **kw):
        try:
            user = request.env.user
            if user.employee_id:
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                img_url = base_url + '/web/image?model=hr.employee.public&id=' + str(
                    user.employee_id.id) + '&field=avatar_128'

                work_location = ''
                if user.employee_id.work_location_id:
                    work_location = user.employee_id.work_location_id.name
                return {
                    'status': 'success',
                    'code': 200,
                    'message': 'Profile retrieved successfully',
                    'data': {
                        "user_id": user.id,
                        "email": user.login,
                        "phone": user.phone,
                        "avatar_url": img_url,
                        "gender": dict(user._fields['emxe_gender'].selection).get(user.emxe_gender),
                        "address": work_location,
                        "language": user.lang,
                        "is_hc_driver": user.transport_vendor_id.is_main_vendor if user.transport_vendor_id else False,
                    }
                }
            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Employee not found",
                    "data": {
                        "success": False
                    }
                }
        except Exception as e:
            return {
                "status": "fail",
                "code": 400,
                "message": e,
                "data": {
                    "success": False
                }
            }

    @http.route('/emxe_api/update_employee_profile', auth='user', csrf=False, type='json')
    def update_employee_profile(self, **kw):
        try:
            user = request.env.user
            if user.employee_id:
                email = kw.get('email')
                phone = kw.get('phone')
                avatar_url = kw.get('avatar_url')
                gender = kw.get('gender')
                address = kw.get('address')
                language = kw.get('language')
                user_update_data = {}
                if email:
                    user_update_data.update({'login': email})
                if phone:
                    user_update_data.update({'phone': phone})
                if gender:
                    user_update_data.update({'emxe_gender': gender})
                if language:
                    user_update_data.update({'lang': language})
                user.sudo().write(user_update_data)
                if address:
                    user.employee_id.work_location_id.name = address

                return {
                    "status": "success",
                    "code": 200,
                    "message": "Cập nhật thành công",
                    "data": {
                        "success": True
                    }
                }

            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Employee not found",
                    "data": {
                        "success": False
                    }
                }

        except Exception as e:
            return {
                "status": "fail",
                "code": 400,
                "message": e,
                "data": {
                    "success": False
                }
            }

    @http.route('/emxe_api/reset_password', auth='user', csrf=False, type='json')
    def reset_password(self, **kw):
        try:
            user = request.env.user
            current_password = kw.get('current_password')
            new_password = kw.get('new_password')
            if not current_password:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu current_password",
                    "data": {
                        "success": False
                    }
                }
            if not new_password:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu new_password",
                    "data": {
                        "success": False
                    }
                }
            check_pass = False
            try:
                db = request.env['ir.config_parameter'].sudo().get_param('odoo.database', 'odoo_emxe')
                request.session.authenticate(db, user.login, current_password)
                check_pass = True
            except Exception as ex:
                check_pass = False
            if check_pass:
                user._change_password(new_password)
                return {
                    "status": "success",
                    "code": 200,
                    "message": "Cập nhật thành công",
                    "data": {
                        "success": True
                    }
                }
            else:
                return {
                    "status": "fail",
                    "code": 300,
                    "message": "Sai password",
                    "data": {
                        "success": False
                    }
                }
        except Exception as e:
            return {
                "status": "fail",
                "code": 400,
                "message": e,
                "data": {
                    "success": False
                }
            }

    def state_convert(self, state=False, trip=False):
        if state == 'done':
            return 7
        if trip.cost_submited:
            return 6
        if state == 'waiting':
            if trip.driver_accept:
                return 2
            else:
                return 1
        if state == 'processing':
            if not trip.trip_pause_time:
                return 3
            else:
                return 4
        if state == 'payment':
            return 5

    @http.route('/emxe_api/get_list_trip', auth='user', csrf=False, type='json')
    def get_list_trip(self, **kw):
        try:
            user = request.env.user
            date_from = kw.get('date_from')
            if date_from:
                date_from = datetime.strptime(f'{date_from} 00:00:00', '%d/%m/%Y %H:%M:%S') - timedelta(hours=7)
            # else:
            #     return {
            #         "status": "fail",
            #         "code": 400,
            #         "message": "Thiếu date_from",
            #         "data": {
            #             "success": False
            #         }
            #     }
            date_to = kw.get('date_to')
            if date_to:
                date_to = datetime.strptime(f'{date_to} 23:59:59', '%d/%m/%Y %H:%M:%S') - timedelta(hours=7)
            # else:
            #     return {
            #         "status": "fail",
            #         "code": 400,
            #         "message": "Thiếu date_to",
            #         "data": {
            #             "success": False
            #         }
            #     }
            index = kw.get('index')
            if index == None:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu index",
                    "data": {
                        "success": False
                    }
                }
            offset = kw.get('offset')
            if offset == None:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu offset",
                    "data": {
                        "success": False
                    }
                }
            state = kw.get('state')
            if not state:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu state",
                    "data": {
                        "success": False
                    }
                }
            domain = [
                ('driver_id', '=', user.id)
            ]
            if date_from:
                domain.append(('start_time', '>=', date_from))
            if date_to:
                domain.append(('start_time', '<=', date_to))
            if state == 'all':
                domain.append(('state', 'in', ['waiting', 'processing', 'payment', 'done']))
            elif state == 'ready':
                domain.append(('state', '=', 'waiting'))
            elif state == 'in_progress ':
                domain.append(('state', '=', 'processing'))
            elif state == 'done':
                domain.append(('state', 'in', ['payment']))
                domain.append(('cost_submited', '=', False))
            elif state == 'paid':
                domain.append('|')
                domain.append(('state', '=', 'done'))
                domain.append(('cost_submited', '=', True))
            list_trip = request.env['hc.trip'].search(domain, order='start_time desc')
            if len(list_trip) > index:
                list_trip = list_trip[index:index+offset]
            else:
                list_trip = request.env['hc.trip']

            result = []
            for trip in list_trip:
                trip_data = {
                    "id": trip.id,
                    "name": f"{trip.pick_up_place} - {trip.destination}",
                    "driver_accept": trip.driver_accept,
                    "start_time": trip.start_time + timedelta(hours=7) if trip.start_time else '',
                    "start_in": trip.pick_up_place if trip.pick_up_place else '',
                    "finish_in": trip.destination if trip.destination else '',
                    "state": self.state_convert(trip.state, trip),
                }
                result.append(trip_data)

            return {
                'status': 'success',
                'code': 200,
                'message': 'success',
                'data': result
            }
        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,

            }

    @http.route('/emxe_api/get_trip_detail', auth='user', csrf=False, type='json')
    def get_trip_detail(self, **kw):
        try:
            user = request.env.user
            id = kw.get('id')
            if id:
                trip = request.env['hc.trip'].search([('id', '=', int(id))])
                if trip:
                    payment_status = ''
                    has_paid = sum(trip.income_detail_ids.filtered(lambda x: x.income_id.name in ['Lái xe thu tiền', 'Khách hàng thanh toán']))
                    if has_paid > 0:
                        payment_status = 2
                    else:
                        payment_status = 1
                    # if trip.remain_customer_amount > 0:
                    #     if trip.remain_customer_amount != trip.customer_amount:
                    #         payment_status = 2
                    #
                    #     else:
                    #         payment_status = 1
                    # else:
                    #     payment_status = 3

                    result = {
                        "id": trip.id,
                        "name": f"{trip.pick_up_place} - {trip.destination}",
                        "driver_accept": trip.driver_accept,
                        "start_time": trip.start_time + timedelta(hours=7) if trip.start_time else '',
                        "start_in": trip.pick_up_place if trip.pick_up_place else '',
                        "finish_in": trip.destination if trip.destination else '',
                        "state": self.state_convert(trip.state, trip),
                        "payment_status": payment_status,
                        "tour_guide": trip.tour_guide if trip.tour_guide else '',
                        "phone": trip.tour_guide_phone if trip.tour_guide_phone else '',
                        "transport_vendor": trip.transport_vendor_id.name if trip.transport_vendor_id else '',
                        "vehicle_number": trip.vehicle_id.license_plate if trip.vehicle_id else '',
                        "vehicle_type": trip.vehicle_id.type.name if trip.vehicle_id else '',
                        "note": trip.note if trip.note else '',
                        "amount": trip.customer_amount if trip.customer_amount else 0,
                    }
                    return {
                        'status': 'success',
                        'code': 200,
                        'message': 'success',
                        'data': result
                    }
                else:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Không tìm thấy chuyến đi",
                        "data": {
                            "success": False
                        }
                    }
            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu id",
                    "data": {
                        "success": False
                    }
                }

        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,

            }

    @http.route('/emxe_api/trip_approval', auth='user', csrf=False, type='json')
    def trip_approval(self, **kw):
        try:
            user = request.env.user
            id = kw.get('id')
            if not id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu id",
                    "data": {
                        "success": False
                    }
                }
            if 'accept' not in kw:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu accept",
                    "data": {
                        "success": False
                    }
                }
            accept = kw.get('accept')

            trip = request.env['hc.trip'].search([('id', '=', int(id))])
            if trip:
                if trip.driver_id != user:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Bạn không phải tài xế được phân công cho chuyến xe này.",
                        "data": {
                            "success": False
                        }
                    }
                if trip.state != 'waiting':
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Chỉ nhận được chuyến ở trạng thái Sắp khởi hành",
                        "data": {
                            "success": False
                        }
                    }
                if accept:
                    trip.sudo().driver_accept = True
                else:
                    trip.sudo().action_draft_trip()
                    if trip.operator_id:
                        hc_code = trip.hc_code if trip.hc_code else ''
                        message = f'Chuyến xe {hc_code} đã bị tài xế từ chối nhận'
                        trip.message_post(body=message, message_type='notification',
                                          partner_ids=[trip.operator_id.partner_id.id])
                return {
                    'status': 'success',
                    'code': 200,
                    'message': 'success',
                    "data": {
                        "success": True
                    }
                }
            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Không tìm thấy chuyến đi",
                    "data": {
                        "success": False
                    }
                }

        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,

            }

    @http.route('/emxe_api/trip_start', auth='user', csrf=False, type='json')
    def trip_start(self, **kw):
        try:
            user = request.env.user
            id = kw.get('id')
            if not id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu id",
                    "data": {
                        "success": False
                    }
                }

            trip = request.env['hc.trip'].search([('id', '=', int(id))])
            if trip:
                if trip.driver_id != user:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Bạn không phải tài xế được phân công cho chuyến xe này.",
                        "data": {
                            "success": False
                        }
                    }
                if trip.state != 'waiting':
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Chỉ được bắt đầu chuyến ở trạng thái Sắp khởi hành",
                        "data": {
                            "success": False
                        }
                    }
                trip.sudo().mark_as_processing()
                trip.sudo().start_time_actual = datetime.now()
                return {
                    'status': 'success',
                    'code': 200,
                    'message': 'success',
                    "data": {
                        "success": True
                    }
                }
            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Không tìm thấy chuyến đi",
                    "data": {
                        "success": False
                    }
                }

        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,

            }

    @http.route('/emxe_api/trip_finish', auth='user', csrf=False, type='json')
    def trip_finish(self, **kw):
        try:
            user = request.env.user
            id = kw.get('id')
            if not id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu id",
                    "data": {
                        "success": False
                    }
                }

            trip = request.env['hc.trip'].search([('id', '=', int(id))])
            if trip:
                if trip.driver_id != user:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Bạn không phải tài xế được phân công cho chuyến xe này.",
                        "data": {
                            "success": False
                        }
                    }
                if trip.state != 'processing':
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Chỉ được kết thúc chuyến ở trạng thái Đang thực hiện",
                        "data": {
                            "success": False
                        }
                    }
                trip.sudo().mark_as_payment()
                trip.sudo().end_time_actual = datetime.now()
                return {
                    'status': 'success',
                    'code': 200,
                    'message': 'success',
                    "data": {
                        "success": True
                    }
                }
            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Không tìm thấy chuyến đi",
                    "data": {
                        "success": False
                    }
                }

        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,

            }

    @http.route('/emxe_api/trip_stop', auth='user', csrf=False, type='json')
    def trip_stop(self, **kw):
        try:
            user = request.env.user
            id = kw.get('id')
            if not id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu id",
                    "data": {
                        "success": False
                    }
                }

            trip = request.env['hc.trip'].search([('id', '=', int(id))])
            if trip:
                if trip.driver_id != user:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Bạn không phải tài xế được phân công cho chuyến xe này.",
                        "data": {
                            "success": False
                        }
                    }
                if trip.state != 'processing':
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Chỉ được tạm dừng chuyến ở trạng thái Đang thực hiện",
                        "data": {
                            "success": False
                        }
                    }
                now = datetime.now()
                trip.sudo().trip_pause_time = now
                return {
                    'status': 'success',
                    'code': 200,
                    'message': 'success',
                    "data": {
                        "success": True
                    }
                }
            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Không tìm thấy chuyến đi",
                    "data": {
                        "success": False
                    }
                }

        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,

            }

    @http.route('/emxe_api/trip_continue', auth='user', csrf=False, type='json')
    def trip_continue(self, **kw):
        try:
            user = request.env.user
            id = kw.get('id')
            if not id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu id",
                    "data": {
                        "success": False
                    }
                }

            trip = request.env['hc.trip'].search([('id', '=', int(id))])
            if trip:
                if trip.driver_id != user:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Bạn không phải tài xế được phân công cho chuyến xe này.",
                        "data": {
                            "success": False
                        }
                    }
                if trip.state != 'processing':
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Chỉ được tiếp tục chuyến ở trạng thái Đang thực hiện",
                        "data": {
                            "success": False
                        }
                    }
                now = datetime.now()
                if trip.trip_pause_time:
                    trip.pause_time_count += (now - trip.trip_pause_time).seconds
                trip.sudo().trip_pause_time = False
                return {
                    'status': 'success',
                    'code': 200,
                    'message': 'success',
                    "data": {
                        "success": True
                    }
                }
            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Không tìm thấy chuyến đi",
                    "data": {
                        "success": False
                    }
                }

        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,

            }

    @http.route('/emxe_api/qr_render', auth='user', csrf=False, type='json')
    def qr_render(self, **kw):
        try:
            user = request.env.user
            trip_id = kw.get('trip_id')
            if not trip_id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu trip_id",
                    "data": {
                        "success": False
                    }
                }
            trip_id = request.env['hc.trip'].search([('id', '=', int(trip_id))])
            if not trip_id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": f"Không tìm thấy chuyến xe có id là {trip_id}",
                    "data": {
                        "success": False
                    }
                }
            amount = kw.get('amount')
            if not amount:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu amount",
                    "data": {
                        "success": False
                    }
                }

            hc_vendor_id = request.env['hc.transport.vendor'].search([('is_main_vendor', '=', True)], limit=1)
            if not hc_vendor_id or not hc_vendor_id.bank_account_ids:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Chưa cấu hình tài khoản ngân hàng cho nhà xe",
                    "data": {
                        "success": False
                    }
                }
            bank_acc_id = hc_vendor_id.bank_account_ids[0]
            qr_code = f'https://img.vietqr.io/image/{bank_acc_id.bank_name}-{bank_acc_id.name}-compact2.png?amount={amount}&addInfo={trip_id.hc_code}'

            return {
                'status': 'success',
                'code': 200,
                'message': 'success',
                "data": {
                    "qr_code": qr_code
                }
            }

        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,

            }

    @http.route('/emxe_api/submit_payment', auth='user', csrf=False, type='json')
    def submit_payment(self, **kw):
        try:
            user = request.env.user
            trip_id = kw.get('trip_id')
            if not trip_id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu trip_id",
                    "data": {
                        "success": False
                    }
                }
            trip_id = request.env['hc.trip'].search([('id', '=', int(trip_id))])
            if not trip_id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": f"Không tìm thấy chuyến xe có id là {trip_id}",
                    "data": {
                        "success": False
                    }
                }
            method = kw.get('method')
            if not method:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu method",
                    "data": {
                        "success": False
                    }
                }
            amount = kw.get('amount')
            if not amount:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu amount",
                    "data": {
                        "success": False
                    }
                }
            payment_img = kw.get('payment_img')
            if not payment_img:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu payment_img",
                    "data": {
                        "success": False
                    }
                }
            # create attachment form payment_img
            attachment = request.env['ir.attachment'].create({
                'name': 'Payment Image',
                'datas': payment_img,
                'res_model': 'hc.trip',
                'res_id': trip_id.id,
            })
            if method == 'cash':
                cost_name = 'Lái xe thu tiền'
            else:
                cost_name = 'Khách hàng thanh toán'
            payment_income_id = request.env['hc.trip.entry.config'].search([('name', '=', cost_name)], limit=1)
            if not payment_income_id:
                activity_id = request.env.ref('mail.mail_activity_data_todo').id
                now = (datetime.now() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S")
                request.env['mail.activity'].sudo().create({
                    'activity_type_id': activity_id,
                    'user_id': 2,
                    'res_id': trip_id.id,
                    'res_model_id': request.env['ir.model'].sudo().search([('model', '=', 'hc.trip')], limit=1).id,
                    'summary': f'{now} Ghi nhận Tài xế thu hộ {amount}vnđ KHÔNG thành công do thiếu cấu hình loại chi phí {cost_name}. Admin vui lòng kiểm tra lại.',
                })
                return {
                    "status": "fail",
                    "code": 400,
                    "message": f"Chưa cấu hình loại doanh thu {cost_name}",
                    "data": {
                        "success": False
                    }
                }
            payment_id = request.env['hc.trip.amount.detail'].create({
                'income_payment_record_id': trip_id.id,
                'payment_income_id': payment_income_id.id,
                'payment_amount': float(amount),
            })

            return {
                'status': 'success',
                'code': 200,
                'message': 'success',
                "data": {
                    "success": True
                }
            }

        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,

            }

    @http.route('/emxe_api/get_done_trip_data', auth='user', csrf=False, type='json')
    def get_done_trip_data(self, **kw):
        try:
            user = request.env.user
            id = kw.get('id')
            if id:
                trip = request.env['hc.trip'].search([('id', '=', int(id))])
                if trip:
                    driver_cash_recieved = sum(trip.income_payment_detail_ids.filtered(
                        lambda x: x.payment_income_id.name in ['Lái xe thu tiền', 'Khách hàng thanh toán']).mapped('payment_amount'))

                    costs = []
                    cost_codes = {
                        'an_uong': 'Ăn',
                        'luu_tru': 'Ngủ',
                        'nuoc_uong': 'Nước',
                        'cao_toc': 'Cao tốc',
                        'ben_bai': 'Bến bãi',
                        'rua_xe': 'Rửa xe',
                        'tip': 'Tip',
                        'sua_chua': 'Sửa chữa',
                        'taxi_hdv': 'Taxi HDV',
                        'khac': 'Khác',
                    }
                    for key in cost_codes.keys():
                        cost = sum(trip.driver_cost_ids.filtered(
                            lambda x: x.driver_cost_id.name == cost_codes[key]).mapped('payment_amount'))
                        if cost:
                            payer = trip.driver_cost_ids.filtered(
                                lambda x: x.driver_cost_id.name == cost_codes[key])[0].payer
                            costs.append({
                                "type": key,
                                "amount": cost,
                                "payer": payer
                            })
                    driver_pay = sum(trip.driver_cost_ids.filtered(
                        lambda x: x.payer == 'driver').mapped('payment_amount'))

                    driver_advance = sum(trip.driver_cost_ids.filtered(
                        lambda x: x.payer == 'driver_advance').mapped('payment_amount'))

                    result = {
                        "id": trip.id,
                        "name": f"{trip.pick_up_place} - {trip.destination}",
                        "date": trip.start_time + timedelta(hours=7) if trip.start_time else '',
                        "start_in": trip.pick_up_place if trip.pick_up_place else '',
                        "finish_in": trip.destination if trip.destination else '',
                        "start_time": trip.start_time_actual + timedelta(hours=7) if trip.start_time_actual else '',
                        "end_time": trip.end_time_actual + timedelta(hours=7) if trip.end_time_actual else '',
                        # "trip_distance": trip.distance_actual if trip.distance_actual else 0,
                        "trip_distance": trip.manual_distance if trip.manual_distance else 0,
                        "time_total": trip.total_time_actual if trip.total_time_actual else 0,
                        "costs": costs,
                        "driver_pay": driver_pay,
                        "driver_advance": driver_advance,
                        "driver_cash_recieved": driver_cash_recieved,
                        "note": trip.cost_note if trip.cost_note else '',
                    }
                    return {
                        'status': 'success',
                        'code': 200,
                        'message': 'success',
                        'data': result
                    }
                else:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Không tìm thấy chuyến đi",
                        "data": {
                            "success": False
                        }
                    }
            else:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu id",
                    "data": {
                        "success": False
                    }
                }

        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,

            }

    @http.route('/emxe_api/trip_cost_submit', auth='user', csrf=False, type='json')
    def trip_cost_submit(self, **kw):
        try:
            user = request.env.user
            trip_id = kw.get('id')
            if not trip_id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu id",
                    "data": {
                        "success": False
                    }
                }
            trip_id = request.env['hc.trip'].search([('id', '=', int(trip_id))])
            if not trip_id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": f"Không tìm thấy chuyến xe có id là {trip_id}",
                    "data": {
                        "success": False
                    }
                }
            costs = kw.get('costs')
            if not costs:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu costs",
                    "data": {
                        "success": False
                    }
                }
            km = kw.get('km')
            if not km:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu km",
                    "data": {
                        "success": False
                    }
                }
            trip_id.manual_distance = float(km)
            note = kw.get('note')
            if note:
                trip_id.message_post(body=note)
            for cost in costs:
                type = cost.get('type')
                if not type:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Thiếu type trong costs",
                        "data": {
                            "success": False
                        }
                    }
                amount = cost.get('amount')
                if not type:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Thiếu amount trong costs",
                        "data": {
                            "success": False
                        }
                    }
                payer = cost.get('payer')
                cost_note = cost.get('note')
                if cost_note:
                    trip_id.cost_note = cost_note
                if not payer:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Thiếu payer trong costs",
                        "data": {
                            "success": False
                        }
                    }
                if payer not in ['driver', 'driver_advance']:
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": "Payer chỉ nhận 2 giá trị là driver hoặc driver_advance",
                        "data": {
                            "success": False
                        }
                    }
                cost_codes = {
                    'an_uong': 'Ăn',
                    'luu_tru': 'Ngủ',
                    'nuoc_uong': 'Nước',
                    'cao_toc': 'Cao tốc',
                    'ben_bai': 'Bến bãi',
                    'rua_xe': 'Rửa xe',
                    'tip': 'Tip',
                    'sua_chua': 'Sửa chữa',
                    'taxi_hdv': 'Taxi HDV',
                    'khac': 'Khác',
                }
                cost_name = cost_codes[cost['type']]
                cost_payment_record_id = request.env['hc.trip.entry.config'].search([('name', '=', cost_name)],
                                                                                    limit=1)
                if not cost_payment_record_id:
                    activity_id = request.env.ref('mail.mail_activity_data_todo').id
                    request.env['mail.activity'].sudo().create({
                        'activity_type_id': activity_id,
                        'user_id': 2,
                        'res_id': trip_id.id,
                        'res_model_id': request.env['ir.model'].sudo().search([('model', '=', 'hc.trip')],
                                                                              limit=1).id,
                        'summary': f'Thiếu cấu hình loại chi phí {cost_name}. Admin vui lòng kiểm tra lại.',
                    })
                    return {
                        "status": "fail",
                        "code": 400,
                        "message": f"Chưa cấu hình loại doanh thu {cost_name}",
                        "data": {
                            "success": False
                        }
                    }
                if cost['payer'] == 'driver':
                    existed_cost = trip_id.driver_cost_ids.filtered(lambda x: x.driver_cost_id == cost_payment_record_id)
                    if existed_cost:
                        existed_cost.unlink()
                    payment_id = request.env['hc.trip.amount.detail'].create({
                        'driver_cost_record_id': trip_id.id,
                        'driver_cost_id': cost_payment_record_id.id,
                        'payment_amount': float(amount),
                    })
                else:
                    existed_cost = trip_id.cost_payment_detail_ids.filtered(lambda x: x.paid_cost_id == cost_payment_record_id)
                    if existed_cost:
                        existed_cost.unlink()
                    payment_id = request.env['hc.trip.amount.detail'].create({
                        'cost_payment_record_id': trip_id.id,
                        'paid_cost_id': cost_payment_record_id.id,
                        'payment_amount': float(amount),
                    })
            trip_id.sudo().cost_submited = True

            return {
                'status': 'success',
                'code': 200,
                'message': 'success',
                "data": {
                    "success": True
                }
            }

        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,

            }

    @http.route('/emxe_api/get_balance', auth='user', csrf=False, type='json')
    def get_balance(self, **kw):
        try:
            user = request.env.user
            offset = kw.get('index') if kw.get('index') else 0
            limit = kw.get('offset') if kw.get('offset') else 80
            all_trip_ids = request.env['hc.trip'].search(
                [('driver_id', '=', user.id), ('state', 'in', ['payment', 'done'])])
            trip_ids = request.env['hc.trip'].search(
                [('driver_id', '=', user.id), ('state', 'in', ['payment', 'done'])], offset=offset, limit=limit, order='id desc')
            all_credit_cost = all_trip_ids.cost_payment_detail_ids.filtered(lambda x: x.paid_cost_id.name in ['Tạm ứng cho lái xe', 'Tất toán cho lái xe'])
            driver_salary = sum(all_trip_ids.mapped('driver_salary')) + sum(all_trip_ids.mapped('driver_cost_ids.payment_amount')) - sum(all_credit_cost.mapped('payment_amount'))
            transactions = []
            for trip in trip_ids:
                # driver_advance = sum(trip.cost_payment_detail_ids.filtered(lambda x: x.paid_cost_id.name == 'Tạm ứng cho lái xe').mapped('payment_amount'))
                # driver_cash_recieved = sum(trip.income_payment_detail_ids.filtered(lambda x: x.payment_income_id.name == 'Lái xe thu tiền').mapped('payment_amount'))
                if trip.driver_salary > 0:
                    transactions.append({
                        'type': 'debit',
                        'amount': trip.driver_salary,
                        'datetime': trip.end_time + timedelta(hours=7) if trip.end_time else '',
                        'description': f'Lái xe nhận tiền từ chuyến {trip.hc_code}',
                    })
                for cost in trip.driver_cost_ids:
                    if cost.payment_amount > 0:
                        transactions.append({
                            'type': 'debit',
                            'amount': cost.payment_amount,
                            'datetime': cost.create_date + timedelta(hours=7),
                            'description': f'Lái xe chi tiền cho {cost.driver_cost_id.name} từ chuyến {trip.hc_code}',
                        })
                for cost in trip.cost_payment_detail_ids:
                    if cost.paid_cost_id.name in ['Tạm ứng cho lái xe', 'Tất toán cho lái xe'] and cost.payment_amount > 0:
                        transactions.append({
                            'type': 'credit',
                            'amount': cost.payment_amount,
                            'datetime': cost.create_date + timedelta(hours=7),
                            'description': f'Lái xe nhận tiền từ {cost.paid_cost_id.name} từ chuyến {trip.hc_code}',
                        })
            return {
                "status": "success",
                "code": 200,
                "message": "",
                "data": {
                    "current_balance": driver_salary,
                    "transactions": transactions
                }
            }

        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,
            }

    # submit oil refill
    @http.route('/emxe_api/submit_oil_refill', auth='user', csrf=False, type='json')
    def submit_oil_refill(self, **kw):
        try:
            user = request.env.user
            params = kw
            vehicle_no = params.get('vehicle_no')
            amount = params.get('amount')
            unit_cost = params.get('unit_cost')
            oil_size = params.get('oil_size')
            odo = params.get('odo')
            image = params.get('image')
            if not vehicle_no:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu vehicle_no",
                    "data": {
                        "success": False
                    }
                }
            if not amount:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu amount",
                    "data": {
                        "success": False
                    }
                }
            if not unit_cost:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu unit_cost",
                    "data": {
                        "success": False
                    }
                }
            if not oil_size:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu oil_size",
                    "data": {
                        "success": False
                    }
                }
            if not odo:
                odo = 0
            vehicle = request.env['hc.vehicle'].search([('license_plate', '=', vehicle_no)])
            if not vehicle:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Không tìm thấy xe có biển số này",
                    "data": {
                        "success": False
                    }
                }
            oil_refill = request.env['hc.oil.management'].create({
                'vehicle_id': vehicle.id,
                'amount': amount,
                'price': unit_cost,
                'liter': oil_size,
                'date': datetime.today(),
                'start_km': odo,
                'user_id': user.id,
                'image': image if image else False,
            })
            return {
                "status": "success",
                "code": 200,
                "message": "Cập nhật thành công",
                "data": {
                    "success": True
                }
            }
        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,
            }

    # get oil refill list of user
    @http.route('/emxe_api/get_oil_refill_list', auth='user', csrf=False, type='json')
    def get_oil_refill_list(self, **kw):
        try:
            user = request.env.user
            offset = kw.get('index') if kw.get('index') else 0
            limit = kw.get('offset') if kw.get('offset') else 80
            oil_refill_list = request.env['hc.oil.management'].search([('user_id', '=', user.id)], offset=offset, limit=limit, order='date desc')
            result = []
            for oil_refill in oil_refill_list:
                result.append({
                    'date': oil_refill.date if oil_refill.date else '',
                    'vehicle_no': oil_refill.vehicle_id.license_plate if oil_refill.vehicle_id.license_plate else '',
                    'amount': oil_refill.amount if oil_refill.amount else 0,
                    'unit_cost': oil_refill.price if oil_refill.price else 0,
                    'oil_size': oil_refill.liter if oil_refill.liter else 0,
                })
            return {
                "status": "success",
                "code": 200,
                "message": "success",
                "data": result
            }
        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,
            }

    # api submit reqair vehicle
    @http.route('/emxe_api/submit_repair_vehicle', auth='user', csrf=False, type='json')
    def submit_repair_vehicle(self, **kw):
        try:
            user = request.env.user
            params = kw
            vehicle_no = params.get('vehicle_no')
            amount = params.get('amount')
            note = params.get('note')
            if not vehicle_no:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu vehicle_no",
                    "data": {
                        "success": False
                    }
                }
            if not amount:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu amount",
                    "data": {
                        "success": False
                    }
                }
            if not note:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu note",
                    "data": {
                        "success": False
                    }
                }
            vehicle = request.env['hc.vehicle'].search([('license_plate', '=', vehicle_no)])
            if not vehicle:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Không tìm thấy xe có biển số này",
                    "data": {
                        "success": False
                    }
                }
            repair_vehicle = request.env['hc.repair.management'].create({
                'vehicle_id': vehicle.id,
                'date': datetime.today(),
                'amount': amount,
                'note': note,
                'user_id': user.id,
            })
            return {
                "status": "success",
                "code": 200,
                "message": "Cập nhật thành công",
                "data": {
                    "success": True
                }
            }
        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,
            }

    # get repair vehicle list of user
    @http.route('/emxe_api/get_repair_vehicle_list', auth='user', csrf=False, type='json')
    def get_repair_vehicle_list(self, **kw):
        try:
            user = request.env.user
            offset = kw.get('index') if kw.get('index') else 0
            limit = kw.get('offset') if kw.get('offset') else 80
            repair_vehicle_list = request.env['hc.repair.management'].search([('user_id', '=', user.id)], offset=offset, limit=limit,
                                                                             order='date desc')
            result = []
            for repair_vehicle in repair_vehicle_list:
                result.append({
                    'date': repair_vehicle.date if repair_vehicle.date else '',
                    'vehicle_no': repair_vehicle.vehicle_id.license_plate if repair_vehicle.vehicle_id.license_plate else '',
                    'repair_cost': repair_vehicle.amount if repair_vehicle.amount else 0,
                    'note': repair_vehicle.note if repair_vehicle.note else '',
                })
            return {
                "status": "success",
                "code": 200,
                "message": "success",
                "data": result
            }
        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,
            }

    # api review trip
    @http.route('/emxe_api/review_trip', auth='user', csrf=False, type='json')
    def review_trip(self, **kw):
        try:
            user = request.env.user
            params = kw
            trip_id = params.get('trip_id')
            trip_rate = params.get('trip_rate')
            cus_rate = params.get('cus_rate')
            note = params.get('note')
            if not trip_id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu trip_id",
                    "data": {
                        "success": False
                    }
                }
            if not trip_rate:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu trip_rate",
                    "data": {
                        "success": False
                    }
                }
            if not cus_rate:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu cus_rate",
                    "data": {
                        "success": False
                    }
                }
            trip = request.env['hc.trip'].search([('id', '=', trip_id)])
            if not trip:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Không tìm thấy chuyến xe",
                    "data": {
                        "success": False
                    }
                }
            if not trip.transport_vendor_id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Chuyến xe chưa có nhà xe",
                    "data": {
                        "success": False
                    }
                }
            review = request.env['hc.vendor.review'].create({
                'vendor_id': trip.transport_vendor_id.id,
                'trip_id': trip.id,
                'driver_id': user.id,
                'trip_rate': trip_rate,
                'cus_rate': cus_rate,
                'note': note,
            })
            return {
                "status": "success",
                "code": 200,
                "message": "Cập nhật thành công",
                "data": {
                    "success": True
                }
            }
        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,
            }

    @http.route('/emxe_api/gps_position', auth='user', csrf=False, type='json')
    def gps_position(self, **kw):
        try:
            user = request.env.user
            params = kw
            trip_id = params.get('trip_id')
            latitude = params.get('latitude')
            longitude = params.get('longitude')
            if not trip_id:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu trip_id",
                    "data": {
                        "success": False
                    }
                }
            if not latitude:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu latitude",
                    "data": {
                        "success": False
                    }
                }
            if not longitude:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Thiếu longitude",
                    "data": {
                        "success": False
                    }
                }
            trip = request.env['hc.trip'].search([('id', '=', trip_id)])
            if not trip:
                return {
                    "status": "fail",
                    "code": 400,
                    "message": "Không tìm thấy chuyến xe",
                    "data": {
                        "success": False
                    }
                }
            locate_list = eval(trip.locate_list) if trip.locate_list else []
            last_distance = 0
            for i in range(len(locate_list)):
                if 'is_pause' in locate_list[len(locate_list) - i - 1] and not locate_list[len(locate_list) - i - 1]['is_pause']:
                    last_locate = locate_list[len(locate_list) - i - 1]
                    last_distance = calculate_distance(last_locate['latitude'], last_locate['longitude'], latitude, longitude)
                    break
            locate_list.append({
                'latitude': latitude,
                'longitude': longitude,
                'is_pause': True if trip.trip_pause_time else False,
            })
            trip.locate_list = str(locate_list)

            return {
                "status": "success",
                "code": 200,
                "message": "Cập nhật thành công",
                "data": {
                    "success": True,
                    "last_distance": last_distance
                }
            }
        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,
            }

    # get list vehicle
    @http.route('/emxe_api/get_vehicle_list', auth='user', csrf=False, type='json')
    def get_vehicle_list(self, **kw):
        try:
            user = request.env.user
            # vehicle_list = request.env['hc.vehicle'].search([('driver_id', '=', user.id)])
            result = []
            for vehicle in user.vehicle_ids:
                result.append({
                    'number': vehicle.license_plate if vehicle.license_plate else '',
                    'type': vehicle.type.name if vehicle.type else '',
                    'vendor': vehicle.own_vehicle_id.name if vehicle.own_vehicle_id else '',
                    'fuel_consumption': vehicle.fuel_consumption if vehicle.fuel_consumption else 0,
                })
            return {
                "status": "success",
                "code": 200,
                "message": "success",
                "data": result
            }
        except Exception as e:
            return {
                'status': 'fail',
                'code': 400,
                'message': e,
            }

    @http.route('/emxe_api/add_registration_id', auth='user', csrf=False, type='json')
    def emxe_add_registration_id(self, **kw):
        try:
            _create_flutter_log(request.env, name='add_registration_id', description=str(kw), type='request')
            user = request.env.user
            if kw.get('registration_id'):
                reg = request.env['emxe.mobile.registration.token'].sudo().search(
                    [('token', '=', kw.get('registration_id'))], limit=1)
                if not reg:
                    request.env['emxe.mobile.registration.token'].sudo().create(
                        {
                            'user_id': user.id,
                            'token': kw.get('registration_id'),
                        }
                    )
                else:
                    reg.sudo().write({'user_id': user.id})
                return {
                    "status": "success",
                    "code": 200,
                    "message": "Đăng ký thành công",
                    "data": {
                        "success": True
                    }
                }
        except Exception as e:
            _create_flutter_log(request.env, name='add_registration_id', description=str(e), type='error')
            return {
                "status": "fail",
                "code": 400,
                "message": e,
                "data": {
                    "success": False
                }
            }

    @http.route('/emxe_api/get_notification_message', auth='user', csrf=False, type='json')
    def emxe_get_notification_message(self, **kw):
        try:
            _create_flutter_log(request.env, name='get_notification_message', description=str(kw), type='request')
            user = request.env.user
            message_list = []
            offset = kw.get('index') if kw.get('index') else 0
            limit = kw.get('offset') if kw.get('offset') else 80
            trip_ids = request.env['hc.trip'].search([('driver_id', '=', user.id), ('state', 'in', ['waiting', 'processing', 'payment', 'done'])])
            if user.partner_id:
                message = request.env['mail.message'].search(
                    [('partner_ids', 'in', user.partner_id.id), ('message_type', '=', 'notification'),
                     ('model', 'in', ['hc.trip']), ('res_id', 'in', trip_ids.ids)], offset=offset, limit=limit, order='id desc')
                print(message)
                if len(message) > 0:
                    for mess in message:
                        val = {
                            'create_on': mess.create_date,
                            'message_id': mess.id,
                            'type': 'payment' if 'của bạn đã được hoàn thành' in mess.body else 'trip',
                            'message_name': 'Thông báo',
                            'message_body': strip_html_tags(mess.body) if mess.body else '',
                            'res_id': mess.res_id,
                        }
                        message_list.append(val)
            return {
                "status": "success",
                "code": 200,
                "message": "success",
                "data": message_list
            }


        except Exception as e:
            _create_flutter_log(request.env, name='get_notification_message', description=str(e), type='error')
            return {
                "status": "fail",
                "code": 400,
                "message": e,
                "data": {
                    "success": False
                }
            }


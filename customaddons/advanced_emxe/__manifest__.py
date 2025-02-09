# -*- coding: utf-8 -*-
{
    'name': "advanced_emxe",
    'summary': """Emxe Backend""",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'data/hc_transport_vendor.xml',
        'data/mail_template.xml',
        'security/group.xml',
        'security/ir.model.access.csv',
        'views/webclient_templates.xml',
        'views/master_data_view.xml',
        'views/res_users.xml',
        'views/accountant_views.xml',
        'views/emxe_firebase_config_views.xml',
        'views/emxe_flutter_log_views.xml',
        'views/emxe_mobile_registration_token_views.xml',
        'data/ir_cron_data.xml',
        'wizard/wizard_select_trip_data.xml',
    ],
}

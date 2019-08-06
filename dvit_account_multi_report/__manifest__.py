# -*- coding: utf-8 -*-

{
    'name': 'Accounting Multi Report',
    'version': '10.0.2.2',
    'category': 'Accounting & Finance',
    'author': 'ITGRUPO-COMPATIBLE-BO',
    'summary': 'Accounting Multi Report',
    'website': 'https://dvit.me',
    'depends': ['account_financial_report_qweb'],
    'data': [
        'data/report_paperformat.xml',
        'data/data.xml',
        'data/res_currency_data.xml',
        'report/report.xml',
        'views/view.xml',
        'views/res_currency_views.xml',
        'wizard/wizard.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'images': ['images/main_screenshot.png'],
}

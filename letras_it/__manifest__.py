# -*- coding: utf-8 -*-
{
    'name': "LETRAS IT",

    'summary': """
        Módulo de letras para pago de facturas""",

    'description': """
        Módulo
    """,

    'author': "ITGRUPO-COMPATIBLE-BO",
    'website': "http://www.itgrupo.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'odoope_einvoice_base', 'account_payment_it'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'letras_it.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'auto_install': False,
    'installable': True,
    'application': True
}

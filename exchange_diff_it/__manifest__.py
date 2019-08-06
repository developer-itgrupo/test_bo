# -*- coding: utf-8 -*-
{
    'name': "Exchange Diff IT",

    'summary': """
        Modulo de diferencias de cambio""",

    'description': """
        Modulo de diferencias de cambio
    """,
    'author': "ITGRUPO-COMPATIBLE-BO",
    'category': 'account',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['account','res_currency_rate_it','import_base_it'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',,
        'views/exchange_diff_config_view.xml',
        'views/exchange_diff_view.xml',
        'wizard/selection_wizard_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

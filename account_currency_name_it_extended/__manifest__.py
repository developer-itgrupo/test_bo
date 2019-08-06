# -*- coding: utf-8 -*-

{
    'name': "Currency Name Extended",

    'description': """
    Extensiones al modulo de Currency Name
    """,

    'author': "ITGRUPO-COMPATIBLE-BO",

    # for the full list
    'category': '',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account_parametros_it','account_currency_name_it'],

    # always loaded
    'data': [
        'currency_name_extended_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': []
}
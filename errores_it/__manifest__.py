# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'error IT',
    'category': 'Hidden',
    'version': '1.0',
    'description':
        """
Odoo Web core module.
========================

This module provides the core of the Odoo Web Client.
        """,
    'depends': ['web'],
    'auto_install': False,
    'author': 'ITGRUPO-COMPATIBLE-BO',
    'data': [
    ],
    'qweb': [        
        'static/base.xml'
    ],
    'bootstrap': True,  # load translations for login screen
}

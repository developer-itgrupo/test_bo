# -*- coding: utf-8 -*-
{
    'name': "IT Solutions",

    'summary': """
        Modulo para cambiar la funcionalidad de las opciones a la hora de facturar pedidos de compra""",

    'description': """
        Long description of module's purpose
    """,

    'author': "ITGRUPO-COMPATIBLE-BO",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/purchase_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

# -*- coding: utf-8 -*-
# __openerp__.py
{
    'name': "Reporte excel de Extracto Bancario",
    'category': 'Other',
    'author': 'ITGRUPO-COMPATIBLE-BO',
    'depends': ['account','import_base_it'],
    'version': '1.0',
    'description': """
    - Imprimir reporte en xls
    """,
    'data': [
        'views/account_bank_statement_inherent.xml',
    ],
}

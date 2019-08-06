# -*- coding: utf-8 -*-

{
'name': 'Account Invoice Duplicate Update',
'version': '0.1',
'description': """
Este modulo anexará las facturas duplicadas a sus ordenes de compra respectivas
""",
'author': 'ITGRUPO-COMPATIBLE-BO',
'depends': [
	'account',
	'purchase'
	],
'data': ['account_invoice_duplicate_update_view.xml'],
'init_xml': [],
'demo_xml': [],
'update_xml': [],
'license': 'Other OSI approved licence',
'installable': True,
}
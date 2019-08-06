# -*- encoding: utf-8 -*-
{
	'name': 'Optimizando nota de credito',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','account','sh_message'],
	'version': '1.0',
	'description':"""
			Este modulo anula Factura mal generada y lo rectifica
	""",
	'auto_install': False,
	'demo': [],
	'data':[
		# 'account_invoice_view.xml'
		'wizard/account_invoice_refund_view.xml',
		'account_invoice_reemplazar_view.xml',
		'main_parameter_view.xml',
	],
	'installable': True
}
# -*- encoding: utf-8 -*-
{
	'name': 'Remove Default Description Refund Invoice',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['base','account','account_invoice_it'],
	'version': '1.0.0',
	'description':"""
		Módulo que suprime la funcionalidad de asignar por defecto el campo 'name' de account_invoice al campo 'description' de account_invoice_refund'.
	""",
	'auto_install': False,
	'demo': [],
	'data':	[],
	'installable': True
}

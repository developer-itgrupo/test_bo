# -*- encoding: utf-8 -*-
{
	'name': 'Account Multipayment Invoices IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['account','odoope_einvoice_base','account_parametros_it','analisis_saldos_comprobantes_periodo_it','account_bank_statement_it'],
	'version': '1.0.0',
	'description':"""
	Modulo para permitir el mutipago de facturas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'multipayment_invoice_view.xml',
		],
	'installable': True
}

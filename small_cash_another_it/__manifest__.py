# -*- encoding: utf-8 -*-
{
	'name': 'Small Cash Another IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['import_base_it','anticipo_proveedor_it'],
	'version': '1.0',
	'description':"""
	Modulo de registro de ingresos y egresos en caja chica
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_journal_view.xml', 
			'small_cash_another_view.xml', 
			'account_transfer_view.xml', 
			'voucher_payment_receipt_view.xml', 
			'anticipo_proveedor_view.xml', 
			'account_move_view.xml',
			'small_cash_view_view.xml',
			'anticipo_proveedor_report_view.xml'],
	'installable': True
}

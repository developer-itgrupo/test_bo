# -*- encoding: utf-8 -*-
{
	'name': 'Activos fijos IT',
	'category': 'assets',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['account_asset','sh_message'],
	'version': '1.0',
	'ITGRUPO_VERSION': 2,
	'description':"""
		Módulo para activos fijos.
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_asset_views.xml',
		'views/account_asset_report_view.xml',
		],
	'installable': True
}

# -*- encoding: utf-8 -*-
{
	'name': 'Importacion ventas IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','importacion_extras_it','importacion_compras_it'],
	'version': '1.0',
	'description':"""
		Importacion ventas IT
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/importacion_view.xml'],
	'installable': True
}

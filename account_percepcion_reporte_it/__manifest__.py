# -*- encoding: utf-8 -*-
{
	'name': 'Repaccount Perception IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','account_registro_compra_it','automatic_fiscal_year_it'],
	'version': '1.0',
	'description':"""
		Este modulo crea una vista para las percepciones y su expotacion en forma PI y P en csv
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/account_perception_wizard_view.xml','wizard/account_perception_view.xml'],
	'installable': True
}

# -*- encoding: utf-8 -*-
{
	'name': 'Nuevo Estilo de Orden de Venta IT',
	'category': 'base',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','kardex_it','sale_order_contact'],
	'version': '1.0.0',
	'description':"""
	Cambio de reporte para las cotizaciones y ventas
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/new_sale_reports.xml',
			 'views/new_sale_order_template.xml'],
	'installable': True
}

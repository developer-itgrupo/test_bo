# -*- encoding: utf-8 -*-
{
	'name': 'Product Property IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['stock','menu_consistencia','import_base_it'],
	'version': '1.0',
	'description':"""
	Mostrar las Caracterisicas y Propiedades de los Productos y sus relaciones.
COLUMNAS DE LA VISTA "CARACTERISTICAS PRODUCTOS"    código, descripción, tipo producto, categoría, cuenta ingresos, cuenta gastos, cuenta de entrada, cuenta de salida, cuenta valuación.

	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/product_property_it_view.xml'],
	'installable': True
}

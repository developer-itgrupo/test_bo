
{
    'name': 'Custom Functionality Rates IT',
    'version': '10',
    'license': 'AGPL-3',
    'author': 'ITGRUPO-COMPATIBLE-BO',
    'category': 'Customize',
    'summary': 'Cambios personalizados',
    'depends': ['import_base_it'],
    'data': [
        'views/extended_views.xml',
        'views/sale_tarifa_form.xml',
        'views/extended_product_pricelist_items_views.xml',
        'querys.sql',
    ],
    'installable': True,
}

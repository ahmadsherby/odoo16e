# -*- coding: utf-8 -*-
{
    'name': 'Stone Production',
    'summary': 'This module will handel manufacturing operation of stones starting from Query',
    'version': '0.1',
    'license': "AGPL-3",
    'author': 'Ahmed Sherby, Ahmed Salama',
    'category': 'Inventory/Inventory',
    'depends': ['stock', 'product', 'sale', 'purchase'],
    'data': [
        'data/stone_item_type_data.xml',
        'data/stone_item_choice_data.xml',
        'data/stone_job_order_data.xml',

        'security/stone_production_security.xml',
        'security/ir.model.access.csv',

        'views/res_config_setting_view_changes.xml',
        'views/stone_production_view.xml',
        'views/stone_item_type_view.xml',
        'views/stone_item_color_view.xml',
        'views/stone_item_source_view.xml',
        'views/stone_item_pallet_view.xml',
        'views/stone_item_view.xml',
        'views/product_view_changes.xml',
        'views/stone_job_order_type_view.xml',
        'views/stone_job_order_machine_view.xml',
        'views/stone_job_order_view.xml',
        'views/sale_order_view_changes.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

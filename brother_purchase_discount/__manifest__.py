# -*- coding: utf-8 -*-
{
    'name': "Brothers Purchase Discount",
    'author':
        'Enzapps Private Limited',
    'summary': """
This module will help to assign the targets to sales persons
""",

    'description': """
        Long description of module's purpose
    """,
    'website': "",
    'category': 'base',
    'version': '12.0',
    'depends': ['base','account',"stock","sale","multi_purchase_discount"],
    "images": ['static/description/icon.png'],
    'data': [
        'views/purchase.xml'
           ],
    'demo': [
    ],
    'installable': True,
    'application': True,
}

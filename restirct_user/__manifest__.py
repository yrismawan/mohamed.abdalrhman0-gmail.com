# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'restrict USER',
    'version': '1.0',
    'category': 'Access right',
    'summary': 'restrict USER',
    'author':'BBL',
    'description': """
Using this application you can manage Sales Team  with CRM and/or Sales 
=======================================================================
 """,
    'website': '',
    'depends': ['base','mail'],
    'data': [
             'views/restrict_view.xml','security/user_groups.xml','security/ir.model.access.csv',
             ],
    'qweb': [],
   
    'installable': True,
    'auto_install': False,
}

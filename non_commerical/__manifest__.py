{
    'name': 'Non Commercial Customer',
    'version': '12.0.1.0.0',
    "category": "Generic Modules/Sales",
    'author': 'BBL',
    'company': 'BusinessBorderlines',
    'website': 'www.BusinessBorderlines.com',
    'depends': ['sale','base','account','sales_regions','sale_custom_discount'],
    'data': ['views/non_commerical_action.xml','views/res_partner.xml','views/non_commerical_menu.xml','secuirty/ir.model.access.csv','secuirty/user_group_rights.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto-install':True,
}

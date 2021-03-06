from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError,UserError
import logging
import datetime as dt
from datetime import datetime, timedelta
import calendar
import re
_logger = logging.getLogger(__name__)
class customer_annual_report(models.Model):
    _name='customer.annual.sales.report'
    name=fields.Char('name',default="Customer Annual Sales Report")
   
    product_id=fields.Many2one('product.product','Product')
    year_selected =fields.Many2many(comodel_name='customer.annual.year.list', relation="year_list", column1="id", column2="name", string="YEAR")
    
    @api.onchange('year_selected')
    def create_list_date(self):
        _logger.info('Change List Date')
        res=[]
        date_list=self.env['customer.annual.year.list'].search([])
        
        for num in range(2000, (datetime.now().year) ):
            res.append(str(num))
            if not date_list.search([('name','=',str(num))]):
                date_list.create({'name':str(num)})
        #self.year_selected=[(2,self.id)]
                 

        _logger.info(res)



    def search_report(self):
        _logger.info('Date from')
        ids=[]
        str_domain=""
         
        
        visits=self.env['sale.order.line'].search([('state','in',['sale','done'])]) 
        res=[] 
        _logger.info(visits)
        if self.year_selected:
            
            for record in self.year_selected:
                _logger.info(record.name)
                for rec in visits :
                    _logger.info(rec.create_date.strftime('%Y'))
                    if int(rec.create_date.strftime('%Y'))==int(record.name) :
                        res.append(rec.id)
                _logger.info(res)
            visits= visits.search([('id','in',res)]) 
        _logger.info(visits) 
        if self.product_id:
            
             
            visits=visits.search(['&',('id','in',visits.ids),('product_id','=',self.product_id.id)])
        
        

        for rec in visits:
            ids.append(rec.id)

        _logger.info(visits)
        pivot_id=self.env.ref('Customer_Annual_Sales_Report.view_customer_annual_pivote').id
        tree_view=self.env.ref('Customer_Annual_Sales_Report.view_customer_annual_tree_line').id

        self = self.with_context(new_value=True)
        _logger.info(self.env.context)
        return { 'name':'/',
        'view_mode': 'tree,pivot', 
        'view_type': 'form',
        'view_id':False,
        'views':[(tree_view,'tree'),(pivot_id,'pivot'),],
        'res_model': 'sale.order.line',
        'target': 'current',
         'domain':"[('id','in',%s)]"%(ids),
         'context':{'group_by':'order_partner_id','default_name_report':'Cuatomer_annual_reprot'},
        'type': 'ir.actions.act_window',
        
         
                   } 
class year_list(models.Model):
    _name="customer.annual.year.list"
    name=fields.Char('Year')
    #year_selected =fields.Selection([(num, str(num)) for num in range(2000, (datetime.now().year)+1 )], 'Year')
class sales_order_line(models.Model):
    _inherit="sale.order.line"
    name_report=fields.Char("name_report")
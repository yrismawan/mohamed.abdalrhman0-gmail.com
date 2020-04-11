from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError,UserError
import logging
import datetime as dt
from datetime import datetime, timedelta
import calendar
import re
_logger = logging.getLogger(__name__)

class sale_rep_visit_count(models.Model):
    _inherit ='res.users'
    year_date=fields.Char('Year',compute='_get_date_det')
    Month_date=fields.Char('Month',compute='_get_date_det')
    planned_count=fields.Integer('Planned Visit')
    complete_count=fields.Integer('Completed Visit')
    cancel_count=fields.Integer('Canceled Visit')
    #sale_visit=fields.One2many('sale.visit','rep',copy=True ,store=True)

    @api.one
    @api.depends('create_date')
    def _get_date_det(self):
        _logger.info('Yeare')
        for rec in self :
            rec.year_date=rec.create_date.strftime('%Y')
            rec.Month_date=rec.create_date.strftime('%m')

class sale_rep_visit_count(models.Model):
    _name='sale.visit.count.report'
    name=fields.Char('name',default="Sales Rep Visits")
    #_inherit="sale.order.line"
    user_id=fields.Many2one('res.users','Sale rep')
   
    Date_from=fields.Date('Date From')
    Date_to=fields.Date('Date To')
    Status = fields.Selection([('Planned','Planned'),('Canceled','Canceled'),('Completed','Completed')],"Status")
    def search_report(self):
       
         
        ids=[]
        str_domain=""
        if self.Date_from and self.Date_to and self.Date_to<=self.Date_from:
            raise ValidationError('Date To must be greater than Date From')
            return True
          
        if self.Date_from and self.Date_to and self.Status :
            visits=self.env['sale.visit'].search(['&',('Status','=',self.Status),'&',('Day','>=',self.Date_from),('Day','<=',self.Date_to)])
        elif self.Date_from and self.Date_to:
            visits=self.env['sale.visit'].search(['&',('Day','>=',self.Date_from),('Day','<=',self.Date_to)])
        elif self.Date_from and self.Status :
            visits=self.env['sale.visit'].search(['&',('Status','=',self.Status),('Day','>=',self.Date_from)])
        
        elif self.Status and self.Date_to:
            visits=self.env['sale.visit'].search(['&',('Status','=',self.Status),('Day','<=',self.Date_to)])
        elif   self.Date_to:
            visits=self.env['sale.visit'].search([('Day','<=',self.Date_to)])
        elif self.Status  :
            visits=self.env['sale.visit'].search([('Status','=',self.Status) ])
        elif   self.Date_from:
            visits=self.env['sale.visit'].search([('Day','>=',self.Date_from)]) 
        else:
            visits=self.env['sale.visit'].search([]) 

        
        for rec in visits:
            rec.rep.planned_count=0
            rec.rep.cancel_count=0
            rec.rep.complete_count=0
        
        for rec in visits:
            
            if rec.Status=='Planned':
                 rec.rep.planned_count+=1
            if rec.Status=='Canceled':
                 rec.rep.cancel_count+=1
            if rec.Status=='Completed':
                 rec.rep.complete_count+=1    
        
        for rec in visits:
            if self.user_id :
                if  self.user_id==rec.rep:
                    ids.append(rec.rep.id)
            else:
                ids.append(rec.rep.id)
         

        

        view_id_tree=self.env.ref('Sales_Rep_Visits_Count_Report.view_sale_visit_count').id
        
       
        return { 'name':'/',
        'view_mode': 'tree', 
        'view_mode': 'tree', 
        'views': [(view_id_tree, 'tree')], 
        'res_model': 'res.users',
        'target': 'current',
         'domain':"[('id','in',%s)]"%(ids),
          
         'context':{ },
        'type': 'ir.actions.act_window',
        
         
                   }   
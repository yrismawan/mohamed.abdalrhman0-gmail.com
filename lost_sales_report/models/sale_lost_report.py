from odoo import api ,models, fields
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError,UserError
import logging 
from datetime import datetime, timedelta,date
import datetime as dt
import calendar
_logger = logging.getLogger(__name__)
class Lost_Report(models.Model):
    _name="lost.sale"
    description="Lost Sale Report"
    name=fields.Char('name',default="Lost Sale Report")
    Date_from=fields.Date('Date From')
    Date_to=fields.Date('Date To')
    user_id=fields.Many2one('res.users','Sale rep')
    cancel_reason=fields.Selection([('A','A'),('B','B')],'Cancelation Reason')
    def search_report(self):
        _logger.info('Date from')
        _logger.info(self.Date_from)
         
        ids=[]
        str_domain=""
        if self.Date_from and self.Date_to and self.Date_to<=self.Date_from:
            raise ValidationError('Date To must be greater than Date From')
            return True
          
        visits=self.env['sale.order'].search([]) 
        res=[] 
        for record in visits:
            res.append((record.id))
        if   self.Date_from:

            _logger.info(visits)
             
            visits=visits.search(['&',('id','in',visits.ids),('create_date','>=',self.Date_from)]) 
        if   self.Date_to:
            _logger.info(visits)
            
            visits=visits.search(['&',('id','in',visits.ids),('create_date','<=',self.Date_to)])
        
        if self.user_id:
            _logger.info(visits)
             
            visits=visits.search(['&',('id','in',visits.ids),('user_id','=',self.user_id.id)])
        if self.cancel_reason:
            _logger.info(visits)
            
            visits=visits.search(['&',('id','in',visits.ids),('reason','=',self.cancel_reason)])    
   
        

        for rec in visits:
            ids.append(rec.id)

        _logger.info(visits)
        view_id = self.env.ref('lost_sales_report.lost_sale_report_tree').id
        
      
        return {
            'name':'Lost Report',
            'view_type':'form',
            'view_mode':'tree',
            'views' : [(view_id,'tree')],
            'res_model': 'sale.order',
             'domain':"[('id','in',%s),('state','=','cancel')]"%(ids),
            'view_id':view_id,
            
            'type':'ir.actions.act_window',
             
            'target': 'current',
            
        }
         
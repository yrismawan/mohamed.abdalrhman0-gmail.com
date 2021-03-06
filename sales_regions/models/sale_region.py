# -*- coding: utf-8 -*-

from odoo import api ,models, fields
import logging
import datetime as dt
from datetime import datetime, timedelta
import calendar
from dateutil import relativedelta
from odoo.exceptions import ValidationError 
_logger = logging.getLogger(__name__)

class sale_region(models.Model):
 _name ='sale.region'
 parent_region = fields.Many2one('sale.region', string='Region Area', copy=False,domain="[('area_check','=',True)]")
 name = fields.Char('Region/Area Name',required=True,Translate=True)
 user_id= fields.Many2many('res.users',string='Region Leader')
 sale_manager=fields.Many2one('res.users',string="Sales Manger",domain="[('groups_id','=',21)]")
 area_check=fields.Boolean("Area")
 area_manager=fields.Many2one('res.users',string="Area Manger",domain="[('groups_id.name','=','User: All Documents')]")
 path_region=fields.Char('Path')
 sale_manager_id=fields.Integer(related="parent_region.sale_manager.partner_id.id",store=True)
 area_manager_id=fields.Integer(related="parent_region.area_manager.partner_id.id",store=True)

 @api.multi
 @api.onchange('area_manager','sale_manager')
 def get_list_of_user(self):
     self.env['ir.cron'].clear_caches()
     _logger.info("Onchange")
     if self.area_manager and self.sale_manager:
       region=self.env['sale.region'].search([])
       current_region=self.env['sale.region'].search([('name','=',self.name)])
       assign_region=[]
       for rec in region:
            parent_reg=rec.path_region
            if str(current_region.id) in parent_reg:
                assign_region.append(rec.id)
      
       assign_region=list(set(assign_region))
       
        
       for reg in assign_region:
                    _logger.info(reg)
                    _logger.info(type(reg))
                   
                    if  current_region.area_manager:
                         result = self._cr.execute('delete from  users_region  where id=%s'%(current_region.area_manager.id))
                    if current_region.sale_manager:
                         result = self._cr.execute('delete from  users_region  where id=%s'%(current_region.sale_manager.id))
                    
                     
 @api.constrains('area_manager','sale_manager')
 def save_list_of_user(self):
     
       _logger.info("constrins")
       region=self.env['sale.region'].search([])
       current_region=self.env['sale.region'].search([('name','=',self.name)])
       assign_region=[]
       parent_reg=""
       if self.area_manager:
           for rec in region:
                parent_reg=rec.path_region
                if str(current_region.id) in parent_reg:
                    assign_region.append(rec.id)
           _logger.info(assign_region)
           if self.parent_region:
                assign_region.append(self.parent_region.id)
           assign_region=list(set(assign_region))
           
            
           for reg in assign_region:
                        _logger.info(reg)
                        _logger.info(type(reg))
                        if self.sale_manager:
                             result = self._cr.execute('update sale_region set sale_manager=%s  where area_check=true and  id=%s'%(self.sale_manager.id,reg)) 
                        result=self.env['sale.region'].search([('id','=',self.id)])
                        if result.parent_region.id!=reg :
                            self.area_manager.sudo().region_user=[(4,reg)]
                            self.sale_manager.sudo().region_user=[(4,reg)]
                             

       records=(self.path_region).split("/")
        
       if not records:
          records=(self.path_region)
       
       for rec in range(0,len(records)):
           result=self.env['sale.region'].search([('id','=',int(records[rec]))])
           _logger.info("result")
           for rec in result:
                 if rec.area_check==True:
                     rec.area_manager.sudo().region_user=[(4,self.id)]
                     rec.sale_manager.sudo().region_user=[(4,self.id)] 
                     
                     
                 
 
                    
       result=self.env['sale.region'].search([('id','in',records)])
      
       


 
  
 @api.constrains('parent_region')
 def get_parent_user_region(self):
      
     self.env['ir.cron'].clear_caches()
     parent1=self.env['sale.region'].search([('id','=',self.parent_region.id)])
     if parent1:
         self.path_region=str(parent1.path_region)+'/'+str(self.id)
          
     else:
         self.path_region=str(self.id)
     

 @api.onchange('user_id')
 def get_user_in_region(self):
     current_region=self.env['sale.region'].search([('name','=',self.name)])
     if  current_region.user_id:
         for x in current_region.user_id:

              result = self._cr.execute('delete from  users_region  where id=%s'%(x.id))
               

 @api.constrains('path_region','user_id')
 def get_user_in_region(self):
        
        current_region=self.env['sale.region'].search([('name','=',self.name)])
        users_list=self.env['res.users'].search([('region_user','in',self.id)])
        for rec  in users_list:
            rec.sudo().region_user=[(2,self.id)]
            rec.sudo().user_list=[(2,rec.partner_id.id)]


        for x in self.user_id:
           x.sudo().region_user=[(4,self.id)]
           x.sudo().user_list=[(4,x.partner_id.id)]
        
       

    

 @api.model
 def create(self, values):
         
        return super(sale_region, self).create(values)

 @api.multi
 def write(self, values):
        
        record=self.search([('id','=',self.id)])
      
        
        return super(sale_region, self).write(values)
 @api.multi
 def unlink(self):
         
         for rec in self:
            records=self.env['sale.region'].search([('parent_region','=',rec.id)])
            if records:
             raise ValidationError(rec.name+' have some of area ')
          
        
         return super(sale_region, self).unlink()
 @api.constrains('name')
 def get_parent(self):
   
     for rec in self.search([]) :
        if self.name.lower() == rec.name.lower() and self.id != rec.id:
            raise ValidationError("Error: Region Name must be unique")
     if not self.parent_region :
          
         self.path_region=str(self.id)
     region=self.env['sale.region'].search([])
     for rec in region:
         if rec.area_check==False and rec.parent_region:
              rec.sale_manager_id=rec.parent_region.sale_manager.partner_id.id
              rec.area_manager_id=rec.parent_region.area_manager.partner_id.id

         """elif rec.area_check==True:
             rec.sale_manager_id=rec.sale_manager.partner_id.id
             rec.area_manager_id=rec.area_manager.partner_id.id"""



    
 @api.one
 @api.depends('parent_region')
 def _get_sale_manager_id(self):
    _logger.info("SDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")
    
    if self.area_check==False and self.parent_region:
        self.sale_manager_id=self.parent_region.sale_manager.partner_id.id

class user(models.Model):
    _inherit='res.users'
    region_user=fields.Many2many('sale.region','users_region','id','region')
    user_list=fields.Many2many('res.partner','users_list','id','partner_id')
    

    @api.constrains('region_user')
    def _get_user_in_list(self):
        _logger.info('LIST USER IN REGION')
        user_ids=self.env['res.users'].search([])
        
        # partner id is differance about user id so i add partner id to add access right sale area
        region=self.env['sale.region'].search([('id','in',self.region_user.ids)])
        user_id=self.env['res.users'].search([('id','=',self.id)])
        for rec in user_id.user_list:
            rec.sudo().user_list=[(2,rec.id)]
        _logger.info("region")
        _logger.info(region)
        _logger.info(user_id)
        user_id.sudo().user_list=[(4,user_id.partner_id.id)]
        for rec in  region:
            if  rec.area_check==True:
             _logger.info(rec.area_check)
             user_id.sudo().user_list=[(4,rec.area_manager.partner_id.id)] 
            if rec.user_id:
                 _logger.info(rec.user_id)
                 for res in rec.user_id:
                     _logger.info("REP")
                     _logger.info(res)
                     user_id.sudo().user_list=[(4,res.partner_id.id)]



    @api.constrains('active')
    def get_parent_user(self):
        if self.active==False:
            parent_region=self.env['sale.region'].search([('user_id','=',self.id)])
            if parent_region:
                raise ValidationError('Error : User is Leader Region cannt be delete')

    
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError,UserError
import logging
import datetime as dt
from datetime import datetime, timedelta
import calendar
import re
from dateutil import relativedelta
_logger = logging.getLogger(__name__)
class product_custom(models.Model):
     _inherit="product.template"
     code_product=fields.Char(string='Product Code')
     @api.constrains('code_product')
     def check_code_product(self):
        if self.code_product:
            if not re.match('^[a-zA-Z0-9()]*$',self.code_product):
                 raise ValidationError('Product Code accepte only letter and number.....')
            for rec in self.search([]) :
                if self.code_product == rec.code_product and self.id != rec.id:
                    raise ValidationError("Error: Product Code must be unique")
           
     @api.constrains('name')
     def get_name_product(self):
        if self.code_product:
            for rec in self.search([]) :
                if self.name.lower() == rec.name.lower() and self.id != rec.id:
                    raise ValidationError("Error: Name must be unique")
          

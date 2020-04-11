from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError,UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import datetime as dt
from datetime import datetime, timedelta
import calendar
import time
import re
from odoo.addons import decimal_precision as dp
from dateutil import relativedelta
import logging
_logger = logging.getLogger(__name__)
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils
    
class sale_custom(models.Model):
    _inherit="sale.order"
    date_valid=fields.Integer('validity ')
    user_id=fields.Many2one('res.users',string="Sales Rep")
    discount_list=fields.Many2one('sales.discount',string='Discount')
    reason=fields.Selection([('A','A'),('B','B')],'Reason')
    comment_cancel=fields.Char('Comment')
    order_date=fields.Date('Order Date',default=dt.datetime.strftime(datetime.today(),'%Y-%m-%d'))
    #region=fields.Many2one(related='user_id.region',string='Region')
    
    
    @api.onchange('order_date')
    def get_order_date(self):
        self.order_date=dt.datetime.strftime(datetime.today(),'%Y-%m-%d')


    @api.onchange('partner_id')
    def get_blacklist(self):
        if self.partner_id.is_blacklist==True:
            raise ValidationError('you can not create sale order for this customer')
    @api.constrains('order_date')
    def get_date(self):
        _logger.info(type(self.order_date))
        _logger.info(type(datetime.today()))
        if self.order_date < dt.datetime.today().date():
            raise ValidationError('Order Date must be greater than Today')
    @api.constrains('reason','comment_cancel')
    def print_message_reason(self):
        message_body= "Customer :"+str(self.partner_id.name) +"<br>"+"  Cancelation Reason: "+str(self.reason) 
        if self.comment_cancel:
            message_body+="<br>"+"  Cancelation Comment: "+str(self.comment_cancel)
        _logger.info('Message')
        _logger.info(message_body)
        #sql="insert into mail_message(body,res_id,model,message_type,create_uid) values("+message_body+","+str(self.id)+",'sale.order','notification',"+ str(self.env.uid)+")"
        #_logger.info(sql)
        #self._cr.execute(sql)
        value={
        'body':message_body,
        'res_id':self.id,
        'model':'sale.order',
        'message_type':'notification',
        }
        if (self.reason and self.comment_cancel) or self.reason:
            self.message_ids.create(value)

    @api.multi
    def action_cancel_order(self):
        self.write({'state': 'cancel'})
        _logger.info('Cancel')
        _logger.info('idddd')
        _logger.info(self.id)
        

        cancel_oreder=self.env['sale.order.cancelled'].search([('cancelled_order','=',self.id)])
        self.env['ir.cron'].clear_caches() 
        res= { 'name':'',
         'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'sale.order.cancelled',
        'target': 'new',
         'view_type': 'form',
        'view_id':self.env.ref('sale_custom.cancel_custom_order_from').id ,
        'tag': 'reload',
        'context':{'default_cancelled_order': self.id},
        'res_id':cancel_oreder.id,
        'flags': {'form': {'action_buttons': True}} ,
        'type': 'ir.actions.act_window', }
        
         
        return res
    @api.onchange('date_valid')
    def change_validity_date_vlid(self):
        _logger.info('Validation')
        if self.date_valid<0:
            raise ValidationError('validity date must be postive value')

 
        if self.date_valid>0:
            self.validity_date=datetime.strftime(dt.datetime.today() +timedelta(days=self.date_valid),'%Y-%m-%d %H:%M')
            _logger.info(self.validity_date)
        """if not self.date_valid and self.create_date:
            self.validity_date= datetime.strftime(self.create_date,'%Y-%m-%d %H:%M')"""
    @api.constrains('date_valid')
    def save_validity_date_vlid(self):
        _logger.info('Validation')
       
        if self.date_valid>0:
            self.validity_date=datetime.strftime(dt.datetime.today() +timedelta(days=self.date_valid),'%Y-%m-%d %H:%M')
            _logger.info(self.validity_date)

    @api.onchange('confirmation_date')
    def get_state_action(self):
        _logger.info('ssssssssssss')
        if self.state=='sale':
            _logger.info('777777777777')
            if self.partner_id.credit_limit<self.amount_total:
                warning_mess = {
                            'title': _('Customer Credit Limit!'),
                            'message' : 'Credit Limit for Customer is less than total sale order'
                        }
                        

                return {'warning': warning_mess}
    @api.multi
    @api.onchange('partner_id')
    def change_parnter(self):
        _logger.info('Change Partner')
        _logger.info(self.partner_id)
        _logger.info(self.partner_id.credit_duration_from)
        _logger.info(self.partner_id.credit_duration_to)
        if self.partner_id:
            if self.partner_id.discount:
                self.discount_list=self.partner_id.discount.id
            if self.partner_id.credit_limit:
                account_move_line=self.env['account.move.line'].search([('partner_id','=',self.partner_id.id)])
                credit=0
                debit=0
                for move in account_move_line:
                    if self.partner_id.property_account_receivable_id.id==move.account_id.id or self.partner_id.property_account_payable_id.id==move.account_id.id:
                        if move.debit:
                            debit+=move.debit
                        else:
                             credit+=move.credit
                balance=debit-credit
                _logger.info('BALANCE CUSTOMER')
                _logger.info(balance)

                if self.partner_id.credit_limit!=0 and self.partner_id.credit_limit<balance:
                        warning_mess = {
                                'title': _('Customer Credit Limit!'),
                                'message' : 'The indebtedness Customer is greater than Credit Limit'
                            }
                            

                        return {'warning': warning_mess}



            if self.partner_id.credit_duration_from and   datetime.strftime(self.partner_id.credit_duration_from,'%Y-%m-%d')>datetime.strftime(dt.datetime.today(),'%Y-%m-%d') :
                warning_mess = {
                            'title': _('Customer Credit Duration!'),
                            'message' : self.partner_id.name+'  is out of credit limit duration From'
                        }
                        

                return {'warning': warning_mess}

            if self.partner_id.credit_duration_to and   datetime.strftime(self.partner_id.credit_duration_to,'%Y-%m-%d')<datetime.strftime(dt.datetime.today(),'%Y-%m-%d') :
                warning_mess = {
                            'title': _('Customer Credit Duration!'),
                            'message' : self.partner_id.name+'  is out of credit limit duration To'
                        }
                return {'warning': warning_mess}        
            
        

    @api.multi
    @api.onchange('order_line','discount','amount_untaxed','amount_tax','discount_list') 
    def get_discount_list(self):
        _logger.info('sdfsdfdsf')
        _logger.info(self.discount_list)
        self.amount_untaxed=0
        self.amount_tax=0
        dif=0
        

        self.update({'amount_untaxed':0,
                        'amount_tax':0,})
        for rec in self.order_line:
                rec.price_subtotal=rec.product_uom_qty*rec.price_unit
                if self.discount_list:
                    if self.discount_list.discount_1:
                         rec.price_subtotal= rec.price_subtotal-((rec.price_subtotal*self.discount_list.discount_1)/100)
                    if self.discount_list.discount_2:
                        rec.price_subtotal=rec.price_subtotal-((rec.price_subtotal*self.discount_list.discount_2)/100)
                    if self.discount_list.discount_3:
                       rec.price_subtotal=rec.price_subtotal-((rec.price_subtotal*self.discount_list.discount_3)/100)
                if rec.discount:
                         rec.price_subtotal= rec.price_subtotal-((rec.price_subtotal*rec.discount)/100)
                self.amount_untaxed+=rec.price_subtotal
                rec.price_total=rec.price_subtotal
                 
                if rec.tax_id :
                    _logger.info('TAXES')
                    _logger.info(rec.tax_id.amount)
                    _logger.info(self.amount_tax)
                    
                    rec.price_total=rec.price_subtotal+rec.price_subtotal*(rec.tax_id.amount/100)
                    #self.amount_tax+=rec.price_subtotal*(rec.tax_id.amount/100)
                    
        self.update({'amount_untaxed':self.amount_untaxed})
        if self.amount_tax:
            self.update({'amount_total':self.amount_untaxed+self.amount_tax})
        else:
            self.update({'amount_total':self.amount_untaxed+self.amount_tax})
                                 

    @api.constrains('order_line') 
    def get_discount_list2(self):
        _logger.info('constrains')
        _logger.info(self.discount_list)
        self.amount_untaxed=0
        self.amount_tax=0
        dif=0
        self.update({'amount_untaxed':0,
                        'amount_tax':0,})
        
        for rec in self.order_line:
                
                rec.price_subtotal=rec.product_uom_qty*rec.price_unit
                if self.discount_list:
                    if self.discount_list.discount_1:
                         rec.price_subtotal= rec.price_subtotal-((rec.price_subtotal*self.discount_list.discount_1)/100)
                    if self.discount_list.discount_2:
                        rec.price_subtotal=rec.price_subtotal-((rec.price_subtotal*self.discount_list.discount_2)/100)
                    if self.discount_list.discount_3:
                       rec.price_subtotal=rec.price_subtotal-((rec.price_subtotal*self.discount_list.discount_3)/100)
                if rec.discount:
                         rec.price_subtotal= rec.price_subtotal-((rec.price_subtotal*rec.discount)/100)
                self.amount_untaxed+=rec.price_subtotal
                rec.price_total=rec.price_subtotal
 

                if rec.tax_id :
                    _logger.info('TAXES')
                    _logger.info(rec.tax_id.amount)
                    _logger.info(self.amount_tax)
                    rec.price_total=rec.price_subtotal+rec.price_subtotal*(rec.tax_id.amount/100)
                    #self.amount_tax+=rec.price_subtotal*(rec.tax_id.amount/100)
                    
        self.update({'amount_untaxed':self.amount_untaxed})
        if self.amount_tax:
            self.update({'amount_total':self.amount_untaxed+self.amount_tax})
        else:
            self.update({'amount_total':self.amount_untaxed+self.amount_tax})

    # override method to create invoice from sales order and add discount model
    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}
        _logger.info('amount_total')
        _logger.info(self.amount_total)
        for order in self:
            _logger.info('Sale create invoice')
            
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
            _logger.info(group_key)
            # We only want to create sections that have at least one invoiceable line
            pending_section = None
         
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue

                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    _logger.info('IN V DA TA')
                    _logger.info(inv_data)
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    _logger.info(order)
                    invoices[group_key] = invoice
                    _logger.info('invoices[group_key]')
                    _logger.info(invoices[group_key])
                    invoices_origin[group_key] = [invoice.origin]
                    invoices_name[group_key] = [invoice.name]
                elif group_key in invoices:
                    _logger.info('else;')
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
                        invoices_name[group_key].append(order.client_order_ref)

                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    _logger.info('QTY LINE')
                    _logger.info(line.qty_to_invoice )
                    if pending_section:
                        pending_section.invoice_line_create(invoices[group_key].id, pending_section.qty_to_invoice)
                        pending_section = None
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoices[group_key]] |= order

        for group_key in invoices:
            _logger.info('FOR')
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
                                       'origin': ', '.join(invoices_origin[group_key]),
                                       'discount':self.discount_list.id})
             
            sale_orders = references[invoices[group_key]]
            if len(sale_orders) == 1:
                invoices[group_key].reference = sale_orders.reference

        if not invoices:
            raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
        _logger.info('Invoice Value')
        _logger.info(invoices)
        _logger.info(invoices.values())
        
        for invoice in invoices.values():
            invoice.compute_taxes()
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_total < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            # Idem for partner
            so_payment_term_id = invoice.payment_term_id.id
            invoice._onchange_partner_id()
            # To keep the payment terms set on the SO
            invoice.payment_term_id = so_payment_term_id
            invoice.message_post_with_view('mail.message_origin_link',
                values={'self': invoice, 'origin': references[invoice]},
                subtype_id=self.env.ref('mail.mt_note').id)
        _logger.info('Final')
        _logger.info(invoices)
        return [inv.id for inv in invoices.values()]
class sale_order_line(models.Model):
    _inherit='sale.order.line'
    discount2=fields.Many2one(related="order_id.discount_list",string='Discount')
    price_total_discount=fields.Float('dd') 
    @api.constrains('product_uom_qty')
    def get_nagtive_value(self):
        if self.product_uom_qty<0:
            raise ValidationError('Order Quantity must be postive value')
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','discount2')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit 
            if line.discount2:
                    if line.discount2.discount_1:
                         price= price-((price*line.discount2.discount_1)/100)
                    if line.discount2.discount_2:
                        price=price-((price*line.discount2.discount_2)/100)
                    if line.discount2.discount_3:
                       price=price-((price*line.discount2.discount_3)/100)
            if line.discount:
                         price= price-((price*line.discount)/100)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
 
    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        _logger.info('FFFFFFFFFFFFFFFFFFF')
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            self.product_packaging = False
            return {}
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.product_id.with_context(
                warehouse=self.order_id.warehouse_id.id,
                lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
            )
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    message =  _('You plan to sell %s %s of %s but you only have %s %s available in %s warehouse.') % \
                            (self.product_uom_qty, self.product_uom.name, self.product_id.name, product.virtual_available, product.uom_id.name, self.order_id.warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.virtual_available, self.product_id.virtual_available, precision_digits=precision) == -1:
                        message += _('\nThere are %s %s available across all warehouses.\n\n') % \
                                (self.product_id.virtual_available, product.uom_id.name)
                        for warehouse in self.env['stock.warehouse'].search([]):
                            quantity = self.product_id.with_context(warehouse=warehouse.id).virtual_available
                            if quantity > 0:
                                message += "%s: %s %s\n" % (warehouse.name, quantity, self.product_id.uom_id.name)
                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message' : message
                    }
                    if warning_mess:
                        return {}

                    #return {'warning': warning_mess}
        return {}


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
class invoice_discount(models.Model):
    _inherit='account.invoice'
    discount=fields.Many2one('sales.discount',string='Discount')
    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        round_curr = self.currency_id.round
        for line in self.invoice_line_ids:
            if not line.account_id:
                continue
            price_unit = line.price_unit 
            if line.discount2:
                    if line.discount2.discount_1:
                                 price_unit=  price_unit-((price_unit*line.discount2.discount_1)/100)
                    if line.discount2.discount_2:
                                price_unit=price_unit-((price_unit*line.discount2.discount_2)/100)
                    if line.discount2.discount_3:
                        price_unit= price_unit-((price_unit*line.discount2.discount_3)/100)
            if line.discount:
                 price_unit= price_unit-((price_unit*line.discount)/100)
            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped
        
class invoice_line_discount(models.Model):
    _inherit='account.invoice.line'
    discount2=fields.Many2one(related='invoice_id.discount',string='Discount')
    #price_untaxes_discount=fields.Float('subtotal',compute="_compute_price")
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice', 'invoice_id.date','discount2')
    def _compute_price(self):
        _logger.info('COMPUTE PRICE')
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit 
        if self.discount2:
            if self.discount2.discount_1:
                         price=  price-((price*self.discount2.discount_1)/100)
            if self.discount2.discount_2:
                        price=price-((price*self.discount2.discount_2)/100)
            if self.discount2.discount_3:
                price= price-((price*self.discount2.discount_3)/100)
        if self.discount:
             price= price-((price*self.discount)/100)

        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
         
        _logger.info('DISCOUNT')
        _logger.info(self.price_subtotal)
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            currency = self.invoice_id.currency_id
            date = self.invoice_id._get_currency_rate_date()
            price_subtotal_signed = currency._convert(price_subtotal_signed, self.invoice_id.company_id.currency_id, self.company_id or self.env.user.company_id, date or fields.Date.today())
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign
         
 
    
 
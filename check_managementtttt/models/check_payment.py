# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions,_
from datetime import date, datetime, time, timedelta
import odoo.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError,UserError
class normal_payments(models.Model):
    _name = 'normal.payments'
    _rec_name = 'name'
    _description = 'Payments'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    def get_user(self):
        return self._uid

    def get_currency(self):
        return self.env['res.users'].search([('id', '=', self.env.user.id)]).company_id.currency_id.id

    payment_No = fields.Char()
    name = fields.Char(string="", required=False, compute="get_title", readonly=True)
    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer Name", required=True)
    payment_date = fields.Datetime(string="Payment Date", required=True, default=datetime.today())
    amount = fields.Float(string="Amount",compute="change_checks_ids", store=True )
    amount1 = fields.Float(string="Amount")
    payment_method = fields.Many2one(comodel_name="account.journal", string="Payment Journal", required=True,
                                     domain=[('payment_subtype', 'in', ('issue_check', 'rece_check'))])
    payment_subtype = fields.Selection(related='payment_method.payment_subtype')
    user_id = fields.Many2one(comodel_name="res.users", default=get_user)
    currency_id = fields.Many2one(comodel_name="res.currency", default=get_currency)
    state = fields.Selection(selection=[('draft', 'Draft'), ('posted', 'Posted'), ], default='draft',
                             track_visibility='onchange')
    pay_check_ids = fields.One2many('native.payments.check.create', 'nom_pay_id', string=_('Checks'))
    send_rec_money = fields.Selection(string="Payment Type",selection=[('send','Send Cheques'),('rece','Receive Cheques')],default='rece')
    receipt_number = fields.Char(string="Receipt Number")
    journal_id_account=fields.Many2one(comodel_name="account.journal", string="Journal")
    account_id = fields.Many2one(related="journal_id_account.default_debit_account_id",string="Account Payable",domain="[('user_type_id.type','!=','view')]")
    analyitc_id = fields.Many2one('account.analytic.account',string="Analytic Account",required=True)
    safe_number = fields.Char(string="رقم الحافظة",required=True)
    reff_number= fields.Char(string="reff number",required=True)
    sales_rep = fields.Many2one("res.users", string="sales rep",required=True)

    _sql_constraints = [('reff_number_unique', 'unique(reff_number)', 'Ref.Number already exists!')]

    logo=fields.Binary(related="partner_id.company_id.logo")
    payment_related_journal=fields.Boolean('Payment related journal' ,default=False)
    name_check=fields.Char(default='')

    
    
    @api.multi
    @api.constrains('amount')
    def _total_amount(self):
        if self.payment_subtype:
            if (self.amount) ==0.0 :
                raise exceptions.ValidationError('amount for checks must be more than zerO!')
        else:
            if (self.amount1) ==0.0 :
                raise exceptions.ValidationError('amount for payment must be more than zerO!')



    @api.onchange('partner_id')
    def get_partner_acc(self):
        if self.partner_id and not self.sales_rep:
            self.sales_rep=self.partner_id.user_id.id

        
        """if self.send_rec_money == 'send':
            self.account_id = self.partner_id.property_account_payable_id.id
        elif self.send_rec_money == 'rece':
            self.account_id = self.partner_id.property_account_receivable_id.id"""

    @api.multi
    @api.depends('pay_check_ids')
    def change_checks_ids(self):
        for rec in self:
            tot_amnt = 0.0
            if rec.sudo().payment_subtype:
                if rec.sudo().pay_check_ids:
                    for x in rec.sudo().pay_check_ids:
                        tot_amnt += x.amount
            rec.amount = tot_amnt

    @api.multi
    def button_journal_entries(self):
        return {
            'name': ('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('jebal_con_pay_id', 'in', self.ids)],
        }

    @api.one
    @api.depends('partner_id')
    def get_title(self):
        if self.partner_id :
            if self.payment_method.payment_subtype=='issue_check'  and self.payment_method:
                self.name = "Cheques for  Customer " + str(self.partner_id.name)
            if self.payment_method.payment_subtype=='rece_check' and self.payment_method:
                self.name = "Cheques from Customer " + str(self.partner_id.name)
        else:
            self.name = '*'
        return True

    @api.multi
    def action_confirm(self):
        pay_amt = 0
        _logger.info('Confirm')
        if self.payment_subtype:
            pay_amt = self.amount
        else:
            pay_amt = self.amount1
        move = {
            'name': 'Parnter Payment ' + 'Receipt:' + self.receipt_number ,
            'journal_id': self.payment_method.id,
            'ref': self.receipt_number,
            'company_id': self.user_id.company_id.id,
            'cheque':True
        }
        move_line = {
            'name': 'Parnter Payment ' + 'Receipt:' + self.receipt_number ,
            'partner_id': self.partner_id.id,
            'ref': self.receipt_number,
            'jebal_con_pay_id': self.id,
            
        }
        if self.send_rec_money == 'send':
            debit_account = [{'account': self.account_id.id, 'percentage': 100 , 'analyitc_id' : self.analyitc_id.id,}]
            credit_account = [{'account': self.payment_method.default_debit_account_id.id, 'percentage': 100,'analyitc_id' : self.analyitc_id.id, }]
        else:
            credit_account = [{'account': self.account_id.id, 'percentage': 100 , 'analyitc_id' : self.analyitc_id.id,}]
            debit_account = [{'account': self.payment_method.default_debit_account_id.id, 'percentage': 100,'analyitc_id' : self.analyitc_id.id,}]
        self.env['create.moves'].create_move_lines(move=move, move_line=move_line,
                                                   debit_account=debit_account,
                                                   credit_account=credit_account,
                                                   src_currency=self.currency_id,
                                                   amount=pay_amt)
        self.state = 'posted'
        if self.payment_subtype:
            for check in self.pay_check_ids:
                check_line_val = {}
                check_line_val['check_number'] = check.check_number
                check_line_val['check_date'] = check.check_date
                check_line_val['check_payment'] = check.nom_pay_id.payment_date

                check_line_val['check_bank'] = check.bank.id
                check_line_val['dep_bank'] = check.dep_bank.id
                if self.send_rec_money == 'rece':
                    check_line_val['state'] = 'holding'
                    check_line_val['check_type'] = 'rece'
                else:
                    check_line_val['state'] = 'handed'
                check_line_val['amount'] = check.amount
                check_line_val['open_amount'] = check.amount
                check_line_val['type'] = 'regular'
                if self.send_rec_money=='send':
                    check_line_val['check_type'] = 'pay'
                elif self.send_rec_money=='rece':
                    check_line_val['check_type'] = 'rece'
                check_line_val['notespayable_id'] = self.payment_method.default_debit_account_id.id
                check_line_val['notes_rece_id'] = self.payment_method.default_debit_account_id.id
                check_line_val['investor_id'] = self.partner_id.id
                check_line_val['check_id'] = check.id 
                """# relation between check and check.management """

                self.env['check.management'].create(check_line_val)
        return True
    @api.onchange('payment_method')
    def get_payment_method(self):
        if self.payment_method.payment_subtype=='issue_check'  and self.payment_method:
            self.send_rec_money='send'
            self.payment_related_journal=True
            

        elif self.payment_method.payment_subtype=='rece_check' and self.payment_method:
            self.send_rec_money='rece'
            self.payment_related_journal=True
        else:
            self.payment_related_journal=False
    @api.constrains('payment_method')
    def save_payment_method(self):
        if self.payment_method.payment_subtype=='issue_check'  and self.payment_method:
            self.send_rec_money='send'
            self.payment_related_journal=True
            

        elif self.payment_method.payment_subtype=='rece_check' and self.payment_method:
            self.send_rec_money='rece'
            self.payment_related_journal=True
        else:
            self.payment_related_journal=False

    
    @api.constrains('send_rec_money')
    def get_send_rec_money(self):
        _logger.info('dddddddddddddddddddddd')
        self.name_check=''
        id=9999
        
         
        if self.send_rec_money=='send' and self.send_rec_money:
            if len(str( self.id))>=4:
                self.name_check="Iss/Cheq"+str( self.id)
            else:
                for i in range(0,4-len(str(abs(self.id)))):
                    self.name_check+='0'
                self.receipt_number=self.name_check+str(self.id)
                self.name_check="Iss/Cheq"+self.name_check+str(self.id)
        if self.send_rec_money=='rece' and self.send_rec_money:
            if len(str( self.id))>=4:
                self.name_check="Rec/Cheq"+str( self.id)
            else:
                for i in range(0,4-len(str(abs(self.id)))):
                    self.name_check+='0'
                self.receipt_number=self.name_check+str(self.id)
                self.name_check="Rec/Cheq" +self.name_check+str(self.id)
        _logger.info('CHECK NAME')
        _logger.info(type(self.id))
        _logger.info(4-len(str(abs(self.id))))
        _logger.info(self.name_check)
        
    @api.multi
    def unlink(self):
         
         for rec in self:
            
            if rec.state=='posted':
             raise ValidationError('You cannot delete approve payment')
          
        
         return super(sale_region, self).unlink()      
    def print_timesheet(self, data):
         
        data = {}
        data['form'] = self.read(['partner_id'])[0]
        return self.env['report'].get_action(self, 'check_managementtttt.receipt_check_cash_payment', data=data)

class payments_check_create(models.Model):

    _name = 'native.payments.check.create'
    _order = 'check_number asc'

    check_number = fields.Char(string=_("Check number"),required=True)
    check_date = fields.Date(string=_('Check Date'),required=True)
    amount = fields.Float(string=_('Amount'),required=True)
    bank = fields.Many2one('res.bank',string=_("Check Bank Name"))
    dep_bank = fields.Many2one('res.bank',string=_("Depoist Bank"))
    nom_pay_id = fields.Many2one('normal.payments')

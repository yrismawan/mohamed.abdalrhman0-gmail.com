# -*- coding: utf-8 -*-

###############################################################################
#
#    Periodical Sales Report
#
#    Copyright (C) 2019 Aminia Technology
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import api, fields, models


class PeriodicalReportProduct(models.TransientModel):
    _name = "customer.cheques"

     
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date ')
    customer=fields.Many2one('res.partner','Customer',domain="[('customer','=',True)]")
    state = fields.Selection(selection=[('holding','Holding'),('depoisted','Depoisted'),
                                         ('approved','Approved'),('rejected','Rejected')
                                         , ('returned', 'Returned'), ('handed', 'Handed'),
                                        ('debited', 'Debited'),('canceled', 'Canceled'),('cs_return','Cs_return')]
                             ,string='State')
    @api.multi
    def check_report(self):
         
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'customer':self.customer.id,
                'state':self.state


            },
        }
        return self.env.ref('customer_cheques.action_report_customer_cheques').report_action(self, data=data)

################################################################################ -*- coding: utf-8 -*-

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

from odoo import api, models
from dateutil.relativedelta import relativedelta
import datetime
import logging

_logger = logging.getLogger(__name__)


class ReportProductSale(models.AbstractModel):
    _name = "report.customer_statement.customer_statement_report"

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data["form"]["date_from"]
        date_to = data["form"]["date_to"]
        customer = data["form"]["customer"]

        total_sale = 0.0
        period_value = ""
        domain = [("type", "=", "out_invoice")]
        if date_from:
            domain.append(("date_invoice", ">=", date_from))
        if date_to:
            domain.append(("date_invoice", "<=", date_to))
        if customer:
            domain.append(("partner_id", "=", customer))

        list = []
        order_line = []
        inv_list=[]
        invoice_ids = self.env["account.invoice"].search(domain, order="origin asc")

        for inv in invoice_ids:
            if inv.state != "draft":
                date_so = ""

                sale_order = self.env["sale.order"].search([("name", "=", inv.origin)])
                if sale_order:
                    date_so = sale_order.date_order

                for line in inv.invoice_line_ids:

                    list.append(
                        {
                            "so_number": inv.origin,
                            "date_so": date_so,
                            "invoice_number": line.invoice_id.number,
                            "product_id": line.product_id.name,
                            "inv_name": line.invoice_id.name,
                            "date_in": line.invoice_id.date_invoice,
                            "partner": line.invoice_id.partner_id.name,
                            "quantity": line.quantity,
                            "price_unit": line.price_unit,
                            "total": line.price_total,
                            # "note_invoice": line.note_invoice,
                            "global_discount": inv.global_discount,
                            "amount_total": inv.amount_total,
                            "id":inv.id
                           
                        }
                    )
                inv_list.append(
                    {
                        "global_discount": inv.global_discount,
                        "amount_total": inv.amount_total,
                        "partner": inv.partner_id.name,
                        "id":inv.id
                        
                    }
                )

        if len(list) != 0:
            return {
                "doc_ids": data["ids"],
                "doc_model": data["model"],
                "period": period_value,
                "date_from": date_from,
                "date_to": date_to,
                "sale_orders": list,
                "inv_list":inv_list,
                "total_sale": total_sale,
                "customer_name": self.env["res.partner"].search([("id", "=", customer)]).name,
                "data_check": False,
                "name_report":'كشــف حســـاب عميل'
            }
        else:
            return {
                "doc_ids": data["ids"],
                "doc_model": data["model"],
                "period": period_value,
                "date_from": date_from,
                "date_to": date_to,
                "sale_orders": list,
                "inv_list":inv_list,
                "total_sale": total_sale,
                "customer": self.env["res.partner"].search([("id", "=", customer)]).name,
                "data_check": True,
                "name_report":'كشــف حســـاب عميل'
            }


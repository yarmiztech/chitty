from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class AccountMove(models.Model):
    _inherit = "account.move"

    # invoice_cash_rounding_id

    # if new_inv.amount_total > round(new_inv.amount_total):

    def action_post(self):
        if self.amount_total > round(self.amount_total):
            list = []
            self.invoice_cash_rounding_id = self.env['account.cash.rounding'].search([('name','=','Round Down')])
            # self._onchange_recompute_dynamic_lines()
            rounding_line = (0,0,{
                'name': self.env['account.cash.rounding'].search([('name','=','Round Down')]).name,
                # 'move_id': self.id,
                # 'account_id': self.env['account.cash.rounding'].search([('name','=','Round Down')]).loss_account_id.id,
                'account_id': self.env['account.account'].search([('name','=','Loss on Sale of Assets'),('company_id','=',self.env.company.id)]).id,
                'price_unit': -(self.amount_total - round(self.amount_total)),
                'quantity': 1,
                # 'is_rounding_line': True,
                'is_rounding_line_enz': True,
                'sequence': 9999  # always last line
            })
            list.append(rounding_line)

            self.invoice_line_ids = list
        else:
            if self.amount_total < round(self.amount_total):
                list = []
                self.invoice_cash_rounding_id = self.env['account.cash.rounding'].search([('name', '=', 'Round UP')])
                rounding_line = (0,0,{
                    'name': self.env['account.cash.rounding'].search([('name', '=', 'Round UP')]).name,
                    # 'move_id': self.id,
                    # 'account_id': self.env['account.cash.rounding'].search([('name', '=', 'Round UP')]).loss_account_id.id,
                    'account_id': self.env['account.account'].search([('name','=','Loss on Sale of Assets'),('company_id','=',self.env.company.id)]).id,
                    'price_unit': round(self.amount_total) - self.amount_total,
                    'quantity': 1,
                    # 'is_rounding_line': True,
                    'is_rounding_line_enz': True,
                    'sequence': 9999  # always last line
                })
                list.append(rounding_line)

                self.invoice_line_ids = list


        return super(AccountMove, self).action_post()
        #
        # if self.amount_total > round(self.amount_total):
        #     self.invoice_cash_rounding_id = self.env['account.cash.rounding'].search([('name','=','Round UP')])


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_rounding_line_enz = fields.Boolean(help="Technical field used to retrieve the cash rounding line.")

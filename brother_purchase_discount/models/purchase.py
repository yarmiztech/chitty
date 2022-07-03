# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

from datetime import date
from datetime import datetime
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import calendar
import re
import json
from dateutil.relativedelta import relativedelta
import pgeocode
import qrcode
from PIL import Image
from random import choice
from string import digits
import json
import re
import uuid
from functools import partial


class PurchaseDiscounts(models.Model):
    _inherit = "purchase.discounts"
    _description = 'Purchase Discounts'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        my_list = []
        if not self.partner_id:
            self.purchased_lines = False
        else:
            if not self.start_date:
                purchases = self.env['purchase.order'].search(
                    [('invoice_count', '!=', 0), ('month', '=', self.month), ('partner_id', '=', self.partner_id.id),
                     ('state', '=', 'purchase')])
                for po in purchases:
                    for p_line in po.order_line:
                        including_price = 0
                        if p_line.taxes_id:
                            including = p_line.price_unit * p_line.taxes_id.amount / 100
                            including_price = p_line.price_unit + including
                        else:
                            including_price = p_line.price_unit
                        product_line = (0, 0, {
                            'month': po.month,
                            'partner_id': po.partner_id.id,
                            'product_id': p_line.product_id.id,
                            'purchase_line_id': p_line.id,
                            'invoice_id': p_line.invoice_lines[0].mapped('move_id').id,
                            'qty': p_line.product_qty,
                            'total_amount': p_line.price_subtotal,
                            'no_of_bags': p_line.no_of_bags,
                            # 'price': p_line.price_unit,
                            'price': including_price,
                            'date': p_line.date_planned,
                        })
                        # invoice_lines.mapped('invoice_id')
                        my_list.append(product_line)
                self.purchased_lines = my_list
            else:
                purchases = self.env['purchase.order'].search(
                    [('invoice_count', '!=', 0), ('partner_id', '=', self.partner_id.id), ('state', '=', 'purchase'),
                     ('dis_completed', '=', False)])
                for po in purchases:
                    for p_line in po.order_line:
                        product_line = (0, 0, {
                            'month': po.month,
                            'partner_id': po.partner_id.id,
                            'product_id': p_line.product_id.id,
                            'purchase_line_id': p_line.id,
                            'invoice_id': p_line.invoice_lines[0].mapped('move_id').id,
                            'qty': p_line.product_qty,
                            'total_amount': p_line.price_subtotal,
                            'no_of_bags': p_line.no_of_bags,
                            'price': p_line.price_unit,
                            'date': p_line.date_planned,
                        })
                        # invoice_lines.mapped('invoice_id')
                        my_list.append(product_line)
                self.purchased_lines = my_list

    def action_approve(self):
        s_month = 0
        s_qty = 0
        s_addit = 0
        s_target = 0
        s_year = 0
        s_promo = 0
        s_other = 0
        s_price = 0
        s_cash = 0
        for line in self.purchased_lines:
            prev = self.env['purchase.discounts.repo'].search(
                [('partner_id', '=', line.partner_id.id), ('purchase_line_id', '=', line.purchase_line_id.id),
                 ('month', '=', self.month), ('product_id', '=', line.product_id.id)])

            if not prev:
                if self.discount_type == 'month':
                    s_month = self.lumpsum_cost
                if self.discount_type == 'qty_dsc':
                    s_qty = self.lumpsum_cost
                if self.discount_type == 'addit_dsc':
                    s_addit = self.lumpsum_cost
                if self.discount_type == 'target_dsc':
                    s_target = self.lumpsum_cost
                if self.discount_type == 'year_dsc':
                    s_year = self.lumpsum_cost
                if self.discount_type == 'promo_dsc':
                    s_promo = self.lumpsum_cost
                if self.discount_type == 'other_dsc':
                    s_other = self.lumpsum_cost
                if self.discount_type == 'cash':
                    s_cash = self.lumpsum_cost
                if self.discount_type == 'price':
                    s_price = self.lumpsum_cost
                order = self.env['purchase.discounts.repo'].create({
                    'partner_id': line.partner_id.id,
                    'company_id': self.company_id.id,
                    'user_id': self.user_id.id,
                    'month': self.month,
                    'ref_no': self.ref_no,
                    'dis_completed': self.create_date,
                    'lumpsum_disc': self.lumpsum_disc,
                    'avarage_cost': self.avarage_cost,
                    # 'month_dsc': self.lumpsum_cost,
                    'month_dsc': s_month,
                    # 'qty_dsc': self.quantity_cost,
                    'qty_dsc': s_qty,
                    'add_dsc': s_addit,
                    'target_dsc': s_target,
                    'year_dsc': s_year,
                    'promo_dsc': s_promo,
                    'other_dsc': s_other,
                    'purchased_id': self.id,
                    'price_discount': s_price,
                    'cash_discount': s_cash,
                    'purchase_line_id': line.purchase_line_id.id,
                    'product_id': line.product_id.id,
                    'qty': line.qty,
                    'price': line.price,
                })
            else:
                if self.discount_type == 'month':
                    s_month = self.lumpsum_cost
                    prev.month_dsc += s_month
                if self.discount_type == 'qty_dsc':
                    s_qty = self.lumpsum_cost
                    prev.qty_dsc += s_qty
                if self.discount_type == 'addit_dsc':
                    s_addit = self.lumpsum_cost
                    prev.add_dsc += s_addit
                if self.discount_type == 'target_dsc':
                    s_target = self.lumpsum_cost
                    prev.target_dsc += s_target
                if self.discount_type == 'cash':
                    s_cash = self.lumpsum_cost
                    prev.cash_discount += s_cash
                if self.discount_type == 'price':
                    s_price = self.lumpsum_cost
                    prev.price_discount += s_price
                prev.qty += line.qty
                prev.price += line.price
            ###########working journal entries#############

            # for invoi in self.mapped('purchased_lines').mapped('invoice_id'):
            inv_amount = 0
            for invoi in self.mapped('purchased_lines').mapped('invoice_id'):
                po = self.env['purchase.order'].search([('name', '=', invoi.ref)])
                # self.env['account.move.line'].create({'invoice_id':refund.id,'product_id':invoi.invoice_line_ids[0].product_id.id,'quantity':self.lumpsum_disc})
                acc = self.env['account.account'].search([('name', '=', 'Purchase Expense'), ('company_id', '=', 1)]).id
                qty = sum(invoi.invoice_line_ids.mapped('quantity'))
                list = []
                if qty:
                    inv_amount = qty * self.lumpsum_cost
                # self.env['account.move.line'].create({
                list_m = (0, 0, {
                    'product_id': invoi.invoice_line_ids[0].product_id.id,
                    'quantity': 1,
                    'price_unit': inv_amount,
                    # 'move_id': refund.id,
                    'name': 'Lumpsum Discounts',
                    'account_id': acc,
                    'tax_ids': []
                })
                list.append(list_m)
                refund = self.env['account.move'].create(
                    {'purchase_id': po.id, 'partner_id': self.partner_id.id, 'move_type': 'in_refund',
                     'invoice_line_ids': list, 'invoice_date': datetime.today().date()})

                # refund.action_invoice_open()
                refund.action_post()
                for line in refund.invoice_line_ids:
                    j = self.env['account.payment.method'].search([('name', '=', 'Manual')])[0]
                    journal = self.env['account.journal'].search([('name', '=', 'Cash'), ('company_id', '=', 1)])
                    pay_id = self.env['account.payment'].create({'partner_id': refund.partner_id.id,
                                                                 'amount': self.lumpsum_disc,
                                                                 'partner_type': 'customer',
                                                                 'payment_type': 'inbound',
                                                                 'payment_method_id': j.id,
                                                                 'journal_id': journal.id,
                                                                 'ref': 'Lumpsum Discounts',
                                                                 # 'invoice_ids': [(6, 0, refund.ids)]
                                                                 })
                    # pay_id.post()
                self.write({'status': 'done'})

            ##################################################################################


class PurchaseDiscountsRepo(models.Model):
    _inherit = "purchase.discounts.repo"

    after_discount_n = fields.Float(string="Final Price", compute='compute_after_discount')

    def compute_after_discount(self):
        for each in self:
            each.after_discount_n = 0
            if each.price:
                each.after_discount_n = each.price - each.month_dsc - each.qty_dsc - each.add_dsc - each.target_dsc - each.year_dsc - each.promo_dsc - each.other_dsc


class AccountInvoice(models.Model):
    _inherit = "account.move"

    # def default_l10n_in_gst_treatment(self):
    #     if self.partner_id:
    #         self.l10n_in_gst_treatment = self.partner_id.l10n_in_gst_treatment

    l10n_in_gst_treatment = fields.Selection([
            ('regular', 'Registered Business - Regular'),
            ('composition', 'Registered Business - Composition'),
            ('unregistered', 'Unregistered Business'),
            ('consumer', 'Consumer'),
            ('overseas', 'Overseas'),
            ('special_economic_zone', 'Special Economic Zone'),
            ('deemed_export', 'Deemed Export'),
        ], string="GST Treatment",default='unregistered')
    @api.onchange('partner_id')
    def onchange_partner_id_gst(self):
        if self.partner_id:
            if self.partner_id.l10n_in_gst_treatment:
                self.l10n_in_gst_treatment = self.partner_id.l10n_in_gst_treatment

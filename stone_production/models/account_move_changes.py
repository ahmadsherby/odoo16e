# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
grey = '\x1b[38;21m'
yellow = '\x1b[33;21m'
red = '\x1b[31;21m'
bold_red = '\x1b[31;1m'
reset = '\x1b[0m'
green = '\x1b[32m'
blue = '\x1b[34m'
# Ahmed Salama Code Start ---->


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    landed_cost_po_id = fields.Many2one('purchase.order', "Landed Cost PO")
    landed_cost_picking_ids = fields.Many2many(comodel_name='stock.picking', column1='landed_cost_bill_id',
                                               column2='picking_id', relation='landed_cost_bill_picking_id_rel',
                                               string="Landed Cost Pickings")

    def _prepare_landed_cost_lines(self):
        landed_costs_lines = self.line_ids.filtered(lambda line: line.is_landed_costs_line)
        if self.landed_cost_po_id and self.landed_cost_po_id.stone_purchase_type == 'local':
            trans_prod_id = self.env['product.product'].browse(int(self.env['ir.config_parameter'].sudo().get_param(
                'stone_production.stone_po_trans_prod_id')))
            if not trans_prod_id:
                raise UserError(
                    _("Missing PO default Transportation product, please check Stone Production configurations!!!!"))
            price_unit = landed_costs_lines[0].currency_id._convert(
                sum(l.price_subtotal for l in landed_costs_lines),
                landed_costs_lines[0].company_currency_id, landed_costs_lines[0].company_id, landed_costs_lines[0].move_id.date)
            cost_lines = [(0, 0, {
                'product_id': trans_prod_id.id,
                'name': trans_prod_id.name,
                'account_id': trans_prod_id.product_tmpl_id.get_product_accounts()['expense'].id,
                'price_unit': price_unit,
                'split_method': trans_prod_id.split_method_landed_cost or 'equal',
            })]
        else:
            cost_lines = [(0, 0, {
                'product_id': l.product_id.id,
                'name': l.product_id.name,
                'account_id': l.product_id.product_tmpl_id.get_product_accounts()['stock_input'].id,
                'price_unit': l.currency_id._convert(l.price_subtotal, l.company_currency_id, l.company_id,
                                                     l.move_id.date),
                'split_method': l.product_id.split_method_landed_cost or 'equal',

            }) for l in landed_costs_lines]
        return cost_lines

    def _prepare_landed_costs(self):
        cost_lines = self._prepare_landed_cost_lines()
        landed_costs = self.env['stock.landed.cost'].create({
            'vendor_bill_id': self.id,
            'landed_cost_po_id': self.landed_cost_po_id and self.landed_cost_po_id.id or False,
            'picking_ids': self.landed_cost_po_id and self.landed_cost_po_id.picking_ids.ids or False,
            'cost_lines': cost_lines})
        return landed_costs

    def button_create_landed_costs(self):
        """Create a `stock.landed.cost` record associated to the account move of `self`, each
        `stock.landed.costs` lines mirroring the current `account.move.line` of self.
        """
        self.ensure_one()
        landed_costs = self._prepare_landed_costs()
        landed_costs.compute_landed_cost()
        action = self.env["ir.actions.actions"]._for_xml_id("stock_landed_costs.action_stock_landed_cost")
        return dict(action, view_mode='form', res_id=landed_costs.id, views=[(False, 'form')])


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('move_type', 'company_id')
    @api.depends('move_type', 'company_id', 'move_id.landed_cost_po_id')
    def _get_product_domain(self):
        """
        Get Domain or products depend on value of New Products Field
        :return: Valid Ids
        """
        domain = []
        if self.company_id:
            domain = ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)]
        default_move_type = self.env.context.get('default_move_type') or self.move_type
        if default_move_type in ('out_invoice', 'out_refund', 'out_receipt'):
            domain.append(('sale_ok', '=', True))
        elif default_move_type in ('in_invoice', 'in_refund', 'in_receipt'):
            domain.append(('purchase_ok', '=', True))
            if self.move_id.landed_cost_po_id:
                domain.append(('landed_cost_ok', '=', True))
        product_ids = self.env['product.product'].search(domain).ids
        return {'domain': {'product_id': [('id', 'in', product_ids)]}}

    product_id = fields.Many2one(domain=_get_product_domain)

# Ahmed Salama Code End.

# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
igrey = '\x1b[38;21m'
yellow = '\x1b[33;21m'
red = '\x1b[31;21m'
bold_red = '\x1b[31;1m'
reset = '\x1b[0m'
green = '\x1b[32m'
blue = '\x1b[34m'
# Ahmed Salama Code Start ---->


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('landed_cost_bill_ids')
    def _landed_cost_count(self):
        for po in self:
            po.landed_cost_bill_count = len(po.landed_cost_bill_ids)

    stone_production_product_ids = fields.One2many('product.template', 'generated_po_id', "New Products")
    landed_cost_bill_ids = fields.One2many('account.move', 'landed_cost_po_id', "Landed Cost Bills")
    landed_cost_bill_count = fields.Integer(compute=_landed_cost_count)

    # ========== Business methods
    def open_po_new_products(self):
        """
        open new products created on this po
        :return: action view
        """
        self.ensure_one()
        domain = [('purchase_source', '=', True)]
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        default_source = self.env['stone.item.source'].search(domain, limit=1)
        action = self.env["ir.actions.actions"]._for_xml_id('stone_production.stone_production_new_product_action')
        action['context'] = {'default_generated_po_id': self.id, 'default_purchase_ok': True,
                             'default_company_id': self.company_id and self.company_id.id or False,
                             'default_item_vendor_id': self.partner_id and self.partner_id.id or False,
                             'default_source_id': default_source and default_source.id or False,
                             'default_detailed_type': 'product'}
        print("CTX: ", action['context'])
        action['domain'] = [('id', 'in', self.stone_production_product_ids.ids)]
        return action

    def _create_picking(self):
        super(PurchaseOrder, self)._create_picking()
        for order in self:
            if any(pol.item_type_id for pol in order.order_line):
                # This order Contain products related to stone production
                # Todo: set done as reserve to prevent user from change done_qty
                order.picking_ids.action_set_quantities_to_reservation()

    def action_add_landed_cost(self):
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # choose the view_mode accordingly
        invoices = self.landed_cost_bill_ids
        action['domain'] = [('id', 'in', invoices.ids)]
        action['context'] = {'default_company_id': self.company_id and self.company_id.id or False,
                             'default_landed_cost_po_id': self.id,
                             'default_landed_cost_picking_ids': self.picking_ids.ids,
                             'default_move_type': 'in_invoice'}
        return action


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id', 'num_of_pieces', 'piece_size')
    def onchange_product_id(self):
        super().onchange_product_id()

    @api.depends('product_packaging_qty', 'num_of_pieces', 'piece_size')
    def _compute_product_qty(self):
        super(PurchaseOrderLine, self)._compute_product_qty()
        for line in self:
            if line.product_id and line.product_id.item_type_id and line.state != 'done':
                line.product_qty = line.piece_size * line.num_of_pieces

    def _suggest_quantity(self):
        """
        Append Qty needed to work regarding new product lines
        """
        print("num_of_pieces: ", self.num_of_pieces)
        super()._suggest_quantity()
        if self.product_id and self.product_id.item_type_id:
            self.product_qty = self.piece_size * self.num_of_pieces

    @api.depends('product_qty', 'product_uom', 'product_id.item_total_cost')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if not line.product_id or line.invoice_lines:
                continue
            line.price_unit = line.product_id.standard_price
        super()._compute_price_unit_and_date_planned_and_name()

    @api.onchange('item_type_id', 'order_id')
    @api.depends('item_type_id', 'order_id.stone_production_product_ids')
    def _get_product_domain(self):
        """
        Get Domain or products depend on value of New Products Field
        :return: Valid Ids
        """
        domain = []
        if self.order_id.company_id:
            domain = ['|', ('company_id', '=', False), ('company_id', '=', self.order_id.company_id.id)]
        if self.order_id.stone_production_product_ids:
            domain.append(('id', 'in', self.order_id._origin.stone_production_product_ids.mapped('product_variant_id.id')))
        else:
            domain.append(('purchase_ok', '=', True))
            domain.append(('item_type_id', '=', False))
        product_ids = self.env['product.product'].search(domain).ids
        return {'domain': {'product_id': [('id', 'in', product_ids)]}}

    product_id = fields.Many2one(domain=_get_product_domain)
    item_type_id = fields.Many2one(related='product_id.item_type_id')
    item_type_size_eq = fields.Selection(related='item_type_id.size')
    color_id = fields.Many2one(related='product_id.color_id')
    pallet_id = fields.Many2one(related='product_id.pallet_id')
    choice_id = fields.Many2one(related='product_id.choice_id')
    length = fields.Integer(related='product_id.length')
    width = fields.Integer(related='product_id.width')
    height = fields.Integer(related='product_id.height')
    thickness = fields.Float(related='product_id.thickness')
    num_of_pieces = fields.Float(related='product_id.num_of_pieces', store=True)
    piece_size = fields.Float(related='product_id.piece_size')


# Ahmed Salama Code End.

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

    stone_production_product_ids = fields.One2many('product.template', 'generated_po_id', "New Products")


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('product_id', 'product_packaging_qty')
    def _compute_product_qty(self):
        """
        Change Compute Qty
        """
        for line in self:
            print('-----------------in -----------------', line.product_id, line.product_id.item_type_id)
            if line.product_id and line.product_id.item_type_id:
                line.product_qty = line.piece_size * line.num_of_pieces
                print('product_qty: ', line.product_qty)
            else:
                return super()._compute_product_qty()

    @api.depends('product_uom', 'product_qty', 'product_id.uom_id',
                 'product_id.num_of_pieces', 'product_id.piece_size', 'item_type_id')
    def _compute_product_uom_qty(self):
        """
        Change Compute Qty
        """
        super()._compute_product_uom_qty()
        for line in self:
            if line.item_type_id:
                line.product_uom_qty = line.piece_size * line.num_of_pieces
                continue

    @api.depends('product_qty', 'product_uom', 'product_id.item_total_cost')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            line.price_unit = line.product_id.item_total_cost

    @api.onchange('item_type_id', 'order_id')
    @api.depends('item_type_id', 'order_id.stone_production_product_ids')
    def _get_product_domain(self):
        """
        Get Domain or products depend on value of New Products Field
        :return:
        """
        domain = []
        if self.order_id.company_id:
            domain = ['|', ('company_id', '=', False), ('company_id', '=', self.order_id.company_id.id)]
        if self.order_id.stone_production_product_ids:
            domain.append(('id', 'in', self.order_id._origin.stone_production_product_ids.mapped('product_variant_id.id')))
        else:
            domain.append(('purchase_ok', '=', True))
            domain.append(('item_type_id', '=', False))
        print("Domain: ", domain)
        product_ids = self.env['product.product'].search(domain).ids
        print("product_ids: ", product_ids)
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
    num_of_pieces = fields.Float(related='product_id.num_of_pieces')
    piece_size = fields.Float(related='product_id.piece_size')

# Ahmed Salama Code End.

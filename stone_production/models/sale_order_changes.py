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


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # ========== compute methods
    @api.depends('product_id')
    def _compute_available_pieces(self):
        """
        Get Number of pieces from product
        """
        for line in self:
            if line.product_id.item_type_id:
                line.available_pieces = line.product_id.num_of_pieces

    @api.depends('display_type', 'product_id', 'product_packaging_qty',
                 'sale_pieces', 'item_type_id')
    def _compute_product_uom_qty(self):
        """
        Change Compute Qty
        """
        super()._compute_product_uom_qty()
        for line in self:
            if line.item_type_id:
                line.product_uom_qty = line.piece_size * line.sale_pieces
                continue

    item_type_id = fields.Many2one(comodel_name='stone.item.type', string="Type")
    item_color_id = fields.Many2one(comodel_name='stone.item.color', string="Color")

    item_size_eq = fields.Selection(related='item_type_id.size')
    piece_size = fields.Float(related='product_template_id.piece_size')

    available_pieces = fields.Float("Available Pieces", compute=_compute_available_pieces, store=True,)
    sale_pieces = fields.Float("Sale Pieces", default=1)
# Ahmed Salama Code End.

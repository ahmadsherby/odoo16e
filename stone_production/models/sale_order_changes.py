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
                logging.info(yellow +" Ava QTY : %s" % line.product_id.free_qty + reset)
                logging.info(yellow +" Piece size: %s" % line.product_id.piece_size + reset)
                logging.info(green +" AVA Pieces: %s" % (line.product_id.free_qty / line.product_id.piece_size) + reset)
                line.available_pieces = line.product_id.piece_size and line.product_id.free_qty / line.product_id.piece_size or 0.0

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

    @api.constrains('available_pieces', 'sale_pieces')
    def _stone_production_qty(self):
        for rec in self:
            if isinstance(rec.id, int):
                if rec.sale_pieces > rec.available_pieces:
                    raise UserError(_("Sale Pieces %s mustn't be more than Available Pieces %s !!!"
                                      % (rec.sale_pieces, rec.available_pieces)))
                if rec.item_type_id == self.env.ref('stone_production.item_type_block') and rec.sale_pieces < 1:
                    raise UserError(_("Sale Pieces %s of Blocks mustn't be less than 1!!!" % rec.sale_pieces))

    @api.depends('item_type_id')
    @api.onchange('item_type_id')
    def _onchange_product_compute_product_qty(self):
        """
        Reset Product Field
        """
        for line in self:
            if line.item_type_id:
                line.product_id = False
                line.name = False

    item_type_id = fields.Many2one(comodel_name='stone.item.type', string="Type")
    item_color_id = fields.Many2one(comodel_name='stone.item.color', string="Color")
    item_pallet_id = fields.Many2one('stone.item.pallet', "Pallet")
    item_size_eq = fields.Selection(related='item_type_id.size')
    piece_size = fields.Float(related='product_template_id.piece_size')

    available_pieces = fields.Float("Available Pieces", compute=_compute_available_pieces, store=True,)
    sale_pieces = fields.Float("Sale Pieces", default=1)
    length = fields.Integer(related='product_id.length')
    width = fields.Integer(related='product_id.width')
    height = fields.Integer(related='product_id.height')
    thickness = fields.Float(related='product_id.thickness')

# Ahmed Salama Code End.

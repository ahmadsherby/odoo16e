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


class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    item_type_id = fields.Many2one(related='product_id.item_type_id', store=True)
    item_id = fields.Many2one(related='product_id.item_id', store=True)
    item_type_size_eq = fields.Selection(related='item_type_id.size')
    color_id = fields.Many2one(related='product_id.color_id', store=True)
    pallet_id = fields.Many2one(related='product_id.pallet_id', store=True)
    choice_id = fields.Many2one(related='product_id.choice_id', store=True)
    length = fields.Integer(related='product_id.length', store=True)
    width = fields.Integer(related='product_id.width', store=True)
    height = fields.Integer(related='product_id.height', store=True)
    thickness = fields.Float(related='product_id.thickness', store=True)
    num_of_pieces = fields.Float(related='product_id.num_of_pieces', store=True)
    piece_size = fields.Float(related='product_id.piece_size', store=True)
    item_total_size = fields.Float(related='product_id.item_total_size', store=True)

    def action_product_create_item(self):
        """
        Create Items to products without
        """
        self.filtered(lambda mv: mv.item_type_id and not mv.item_id).mapped('product_id.product_tmpl_id').action_create_item()

    @api.onchange('num_of_pieces', 'piece_size')
    @api.depends('move_line_ids.qty_done', 'move_line_ids.product_uom_id', 'move_line_nosuggest_ids.qty_done',
                 'num_of_pieces', 'piece_size')
    def _quantity_done_compute(self):
        super()._quantity_done_compute()
        for move in self:
            if move.item_type_id and move.num_of_pieces and move.state not in ('done', 'cancel'):
                quantity_done = move.piece_size * move.num_of_pieces
                for move_line in move.move_line_ids:
                    move_line.qty_done = quantity_done
                move.quantity_done = quantity_done

# Ahmed Salama Code End.

# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from odoo.addons.stone_production.models.stone_item_type import _eq_selections
igrey = '\x1b[38;21m'
yellow = '\x1b[33;21m'
red = '\x1b[31;21m'
bold_red = '\x1b[31;1m'
reset = '\x1b[0m'
green = '\x1b[32m'
blue = '\x1b[34m'
# Ahmed Salama Code Start ---->


class ProductProduct(models.Model):
    _inherit = 'product.template'

    @api.depends('width', 'length', 'height', 'thickness', 'standard_price',
                 'item_type_id.size', 'num_of_pieces')
    def _compute_size(self):
        """
        Compute size form dimension and total size according to number of pieces
        """
        for rec in self:
            piece_size = 0
            if rec.item_type_id.size == 'volume':
                piece_size = rec.length * rec.width * rec.height / 1000000
            if rec.item_type_id.size == 'surface':
                piece_size = rec.length * rec.width / 10000
            rec.piece_size = piece_size
            piece_cost = piece_size * rec.standard_price
            rec.piece_cost = piece_cost
            rec.item_total_size = piece_size * rec.num_of_pieces
            rec.item_total_cost = piece_cost * rec.num_of_pieces

    def _compute_dim_uom_name(self):
        """ Get the unit of measure to one axe dimension
        """
        product_length_in_feet_param = self.env['ir.config_parameter'].sudo().get_param('product.volume_in_cubic_feet')
        dim_foot = self.env.ref('uom.product_uom_inch')
        dim_meter = self.env.ref('uom.product_uom_cm')
        for rec in self:
            if product_length_in_feet_param == '1':
                dim_uom_id = dim_foot
            else:
                dim_uom_id = dim_meter
            rec.dimension_uom_id = dim_uom_id

    @api.model
    def create(self, vals_list):
        """
        If product is created from stone production use type UOM
        :param vals_list:
        :return:
        """
        if vals_list.get('item_type_id'):
            item_type_id = self.env['stone.item.type'].browse(vals_list.get('item_type_id'))
            if item_type_id:
                vals_list['uom_id'] = item_type_id.size_uom_id.id
                vals_list['uom_po_id'] = item_type_id.size_uom_id.id
                vals_list['piece_size_uom_id'] = item_type_id.size_uom_id.id
        return super().create(vals_list)

    item_id = fields.Many2one('stone.item', "Stone Item")
    item_type_id = fields.Many2one(comodel_name='stone.item.type', string="Stone Type")
    source_id = fields.Many2one(comodel_name='stone.item.source', string="Stone Source")
    color_id = fields.Many2one(comodel_name='stone.item.color', string="Stone Color")
    type_size_uom_id = fields.Many2one(related='item_type_id.size_uom_id')
    dimension_uom_id = fields.Many2one('uom.uom', string="UOM", compute=_compute_dim_uom_name)
    dimension_uom_name = fields.Char(related='dimension_uom_id.name')
    length = fields.Integer('Length', digits='Stock Weight')
    width = fields.Integer('Width', digits='Stock Weight')
    height = fields.Integer('Height', digits='Stock Weight')
    thickness = fields.Float('Thickness', digits='Stock Weight')
    stone_size_eq = fields.Selection(related='item_type_id.size', string="Size Eq")
    piece_size = fields.Float("Piece Size", digits='Stock Weight', compute=_compute_size)
    piece_cost = fields.Float("Piece Cost", digits='Stock Weight', compute=_compute_size)
    piece_size_uom_id = fields.Many2one('uom.uom', "Piece UOM")
    piece_size_uom_name = fields.Char(related='piece_size_uom_id.name')
    num_of_pieces = fields.Float("Pieces", default=1)
    item_total_size = fields.Float("Item Total Size", compute=_compute_size)
    item_total_cost = fields.Float("Item Total Cost", compute=_compute_size)
    choice_id = fields.Many2one('stone.item.choice', "Choice")
    remarks = fields.Text("Remarks")
    pallet_id = fields.Many2one('stone.item.pallet', "Pallet")
    item_vendor_id = fields.Many2one('res.partner', 'Source Vendor')
    generated_po_id = fields.Many2one('purchase.order', "Generated From PO")

# Ahmed Salama Code End.

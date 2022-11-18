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


class StoneItemType(models.Model):
    _name = 'stone.item'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Stone ITem"
    _check_company_auto = True
    _rec_names_search = ['name', 'type_id', 'code', 'parent_id']

    # ========== compute methods
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

    @api.depends('type_id', 'color_id', 'source_id')
    def _compute_code(self):
        """
        Compute code of product item from type/source/color/source serial
        :return:
        """
        for rec in self:
            rec.code="/"
            # next_num = 0
            # if rec.source_id:
            #     next_num = rec.source_id.next_num + 1
            # code = "%s-%s-%s-%s" % (rec.type_id.code, rec.source_id.code, rec.color_id.code, next_num)
            # rec.code = code
            # if code and rec.next_num:
            #     rec.source_id.write({'next_num': next_num})

    @api.depends('weight', 'length', 'height', 'thickness', 'type_id.size', 'num_of_pieces')
    def _compute_size(self):
        """
        Compute size form dimension and total suze according to number of pieces
        """
        for rec in self:
            size_value = 0
            if rec.type_id.size == 'volume':
                size_value = rec.weight * rec.length * rec.height / 1000000
            if rec.type_id.size == 'surface':
                size_value = rec.weight * rec.length / 10000
            rec.size_value = size_value
            rec.total_size = size_value * rec.num_of_pieces

    name = fields.Char("Item")
    code = fields.Char("Code", compute=_compute_code, store=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    parent_id = fields.Many2one('stone.item', "Parent")
    parent_item_code = fields.Char('parent_id.code')
    type_id = fields.Many2one(comodel_name='stone.item.type', string="Type", required=True)
    type_size = fields.Selection(related='type_id.size')
    type_size_uom_id = fields.Many2one(related='type_id.size_uom_id')
    source_id = fields.Many2one(comodel_name='stone.item.source', string="Source", required=True)
    color_id = fields.Many2one(comodel_name='stone.item.color', string="Color", required=True)

    weight = fields.Float('Weight', digits='Stock Weight')
    length = fields.Float('Length', digits='Stock Weight')
    height = fields.Float('Height', digits='Stock Weight')
    thickness = fields.Float('Thickness', digits='Stock Weight')
    size_value = fields.Float("Size", digits='Stock Weight', compute=_compute_size)
    dimension_uom_id = fields.Many2one('uom.uom', string="UOM", compute=_compute_dim_uom_name)

    choice = fields.Char("Choice", required=True)
    num_of_pieces = fields.Float("Pieces")
    total_size = fields.Float("Total Size", compute=_compute_size)

    # =========== Core Methods
    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.code:
                name = '[%s] %s' % (rec.code, name)
            result.append((rec.id, name))
        return result
# Ahmed Salama Code End.

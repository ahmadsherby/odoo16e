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


class ProductProduct(models.Model):
    _inherit = 'product.template'

    item_id = fields.Many2one('stone.item', "Stone Item")
    type_id = fields.Many2one(comodel_name='stone.item.type', string="Stone Type")
    source_id = fields.Many2one(comodel_name='stone.item.source', string="Stone Source")
    color_id = fields.Many2one(comodel_name='stone.item.color', string="Stone Color")
    dimension_uom_id = fields.Many2one('uom.uom', string="UOM")
    width = fields.Float('Width', digits='Stock Weight')
    length = fields.Float('Length', digits='Stock Weight')
    height = fields.Float('Height', digits='Stock Weight')
    thickness = fields.Float('Thickness', digits='Stock Weight')

# Ahmed Salama Code End.

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


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    item_type_id = fields.Many2one(comodel_name='stone.item.type', string="Type")
    item_type_size_eq = fields.Selection(related='item_type_id.size')
    type_size_uom_id = fields.Many2one(related='item_type_id.size_uom_id')
    source_id = fields.Many2one(comodel_name='stone.item.source', string="Source")
    color_id = fields.Many2one(comodel_name='stone.item.color', string="Color")
    length = fields.Integer('Length', digits='Stock Weight')
    width = fields.Integer('Width', digits='Stock Weight')
    height = fields.Integer('Height', digits='Stock Weight')
    thickness = fields.Float('Thickness', digits='Stock Weight')

# Ahmed Salama Code End.

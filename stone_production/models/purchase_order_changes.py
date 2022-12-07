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

    item_type_id = fields.Many2one(related='product_id.item_type_id')
    item_type_size_eq = fields.Selection(related='item_type_id.size')
    color_id = fields.Many2one(related='product_id.color_id')
    length = fields.Integer(related='product_id.length')
    width = fields.Integer(related='product_id.width')
    height = fields.Integer(related='product_id.height')
    thickness = fields.Float(related='product_id.thickness')


# Ahmed Salama Code End.

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


class StockLandedCostInherit(models.Model):
    _inherit = 'stock.landed.cost'

    landed_cost_po_id = fields.Many2one('purchase.order', "PO")

# Ahmed Salama Code End.

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


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    is_transporter = fields.Boolean("Transporter?", help="This flag for users who are transporters")
    tons_trans_cost = fields.Float("Trans Cost/Tons", help="Transportation Cost per Tons")
    trans_multi_factor = fields.Float("Trans Multi Factor", help="Transportation Multiplication Factor")


# Ahmed Salama Code End.

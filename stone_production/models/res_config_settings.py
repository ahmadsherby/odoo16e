# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    stone_finished_good_loc_id = fields.Many2one('stock.location', "Finished Good Location")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stone_finished_good_loc_id = fields.Many2one(related='company_id.stone_finished_good_loc_id',
                                                 string="Finished Good Location", readonly=False,
                                                 domain="[('usage', '=', 'internal'), ('company_id', 'in', [company_id, False])]",
                                                 help="Sets a location to be used on update pieces of the used product.")

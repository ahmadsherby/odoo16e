# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    stone_finished_good_loc_id = fields.Many2one('stock.location', "Finished Good Location")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stone_finished_good_loc_id = fields.Many2one(related='company_id.stone_finished_good_loc_id',
                                                 string="Finished Good Location", readonly=False,
                                                 domain="[('usage', '=', 'internal'), ('company_id', 'in', [company_id, False])]",
                                                 help="Set a location to be used on update pieces of the used product.")
    stone_po_prod_categ_id = fields.Many2one('product.category', "PO. New Product Category", readonly=False,
                                             help="Set a product category to be used by default on po new products.")
    stone_po_trans_prod_id = fields.Many2one('product.template', "PO. Transportation", readonly=False,
                                             domaon="[('landed_cost_ok', '=', True)]",
                                             help="Set a product to be used by default on po transportation.")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['stone_po_prod_categ_id'] = int(self.env['ir.config_parameter'].sudo().get_param(
            'stone_production.stone_po_prod_categ_id'))
        res['stone_po_trans_prod_id'] = int(self.env['ir.config_parameter'].sudo().get_param(
            'stone_production.stone_po_trans_prod_id'))
        return res

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('stone_production.stone_po_prod_categ_id',
                                                         int(self.stone_po_prod_categ_id))
        self.env['ir.config_parameter'].sudo().set_param('stone_production.stone_po_trans_prod_id',
                                                         int(self.stone_po_trans_prod_id))
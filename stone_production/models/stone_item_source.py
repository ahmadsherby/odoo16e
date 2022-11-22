# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
grey = '\x1b[38;21m'
yellow = '\x1b[33;21m'
red = '\x1b[31;21m'
bold_red = '\x1b[31;1m'
reset = '\x1b[0m'
green = '\x1b[32m'
blue = '\x1b[34m'
_eq_selections = [('volume', "Volume equation = (L * W * H)"),
                  ('surface', "Surface equation = (L * W)")]
# Ahmed Salama Code Start ---->


class StoneItemSource(models.Model):
    _name = 'stone.item.source'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Stone Item Source(Query)"
    _rec_names_search = ['name', 'code']

    name = fields.Char("Item Source(Query)", required=True)
    code = fields.Char("Code", required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    color_ids = fields.Many2many(comodel_name='stone.item.color', string="Allowed Colors", required=True,
                                 help="The item colors which can be used on selected products.")
    type_ids = fields.Many2many(comodel_name='stone.item.type', string="Allowed Types", required=True,
                                help="The item type which can be used on selected products.")
    estimate_hour = fields.Integer("Overhead Monthly Estimated Hour")
    next_num = fields.Integer("Serial Next Number", default=1001, required=True,
                              help="The next code to be set on generate product")
    location_id = fields.Many2one('stock.location', 'Location', required=True,
                                  help="Sets a location to be used on update pieces of the used product.")
    item_ids = fields.One2many('stone.item', 'source_id', "Items")

    # =========== Core Methods
    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.code:
                name = '[%s] %s' % (rec.code, name)
            result.append((rec.id, name))
        return result

    def unlink(self):
        """
        Prevent delete code of source that is used on item
        :return: SUPER
        """
        for rec in self:
            if rec.item_ids:
                raise UserError(_("It's not possible to delete item type used on active item %s "
                                  % rec.item_ids.mapped('display_name')))
        return super().unlink()

    def write(self, vals):
        """
        Prevent edit code of source that is used on item
        :param vals: edit vals
        :return: SUPER
        """
        # logging.info(blue + "=== source write vals %s" % str(vals) + reset)
        if vals.get('code'):
            for rec in self:
                if rec.item_ids:
                    raise UserError(_("It's not possible to edit item type code used on active item %s "
                                      % rec.item_ids.mapped('display_name')))
        return super().write(vals)

# Ahmed Salama Code End.

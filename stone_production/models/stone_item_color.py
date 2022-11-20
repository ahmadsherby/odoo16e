# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from random import randint
grey = '\x1b[38;21m'
yellow = '\x1b[33;21m'
red = '\x1b[31;21m'
bold_red = '\x1b[31;1m'
reset = '\x1b[0m'
green = '\x1b[32m'
blue = '\x1b[34m'
_eq_selections = [('volume', "Volume equation = (W * L * H)"),
                  ('surface', "Surface equation = (W * L)")]
# Ahmed Salama Code Start ---->


class StoneItemSource(models.Model):
    _name = 'stone.item.color'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Stone Item Color"
    _rec_names_search = ['name', 'code']

    # =========== Compute Methods
    def _default_color(self):
        return randint(1, 11)

    name = fields.Char("Item Source(Query)", required=True)
    code = fields.Char("Code", required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    color = fields.Integer('Color', default=_default_color)

    # =========== Core Methods
    def unlink(self):
        """
        Prevent delete color of type that is used on item
        :return: SUPER
        """
        source_obj = self.env['stone.item.source']
        for rec in self:
            source_ids = source_obj.search([('color_ids', 'in', rec.id)])
            if source_ids:
                raise UserError(_("It's not possible to delete item color used on active sources %s "
                                  % source_ids.mapped('display_name')))
        return super().unlink()

    def write(self, vals):
        """
        Prevent edit code of color that is used on item
        :param vals: edit vals
        :return: SUPER
        """
        # logging.info(blue + "=== color write vals %s" % str(vals) + reset)
        if vals.get('code'):
            source_obj = self.env['stone.item.source']
            for rec in self:
                source_ids = source_obj.search([('color_ids', 'in', rec.id)])
                # logging.info(blue + "yellow source %s" % source_ids + reset)
                if source_ids:
                    raise UserError(_("It's not possible to edit item color code used on active sources %s "
                                      % source_ids.mapped('display_name')))
        return super().write(vals)
# Ahmed Salama Code End.

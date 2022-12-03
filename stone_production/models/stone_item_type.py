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
_eq_selections = [('volume', "Volume equation = (L * W * H)"),
                  ('surface', "Surface equation = (L * W)")]
# Ahmed Salama Code Start ---->


class StoneItemType(models.Model):
    _name = 'stone.item.type'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Stone ITem Type"
    _rec_names_search = ['name', 'code']

    # ========== compute methods
    @api.depends('size')
    def _compute_size_uom_name(self):
        """ Get the unit of measure to interpret the `volume` field. By default, we consider
            that volumes are expressed in cubic meters. Users can configure to express them in cubic feet
            by adding an ir.config_parameter record with "product.volume_in_cubic_feet" as key
            and "1" as value.
        """
        product_length_in_feet_param = self.env['ir.config_parameter'].sudo().get_param('product.volume_in_cubic_feet')
        cubic_foot = self.env.ref('uom.product_uom_cubic_foot')
        square_foot = self.env.ref('uom.uom_square_foot')
        cubic_meter = self.env.ref('uom.product_uom_cubic_meter')
        square_meter = self.env.ref('uom.uom_square_meter')
        for rec in self:
            if product_length_in_feet_param == '1':
                if rec.size == 'volume':
                    size_uom_name = cubic_foot
                else:
                    size_uom_name = square_foot
            else:
                if rec.size == 'volume':
                    size_uom_name = cubic_meter
                else:
                    size_uom_name = square_meter
            rec.size_uom_id = size_uom_name

    def _default_color(self):
        return randint(1, 11)

    name = fields.Char("Item Type", required=True)
    code = fields.Char("Code", required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    size = fields.Selection(selection=_eq_selections, string="Size Equation", required=True,
                            help="The equation of compute size of item")
    size_uom_id = fields.Many2one('uom.uom', string="UOM", compute=_compute_size_uom_name)
    size_uom_name = fields.Char(related='size_uom_id.name')
    categ_id = fields.Many2one('product.category', 'Product Category', required=True,
                               help="Sets a category to be used on create product.")
    item_ids = fields.One2many('stone.item', 'item_type_id', "Items")
    color = fields.Integer('Color', default=_default_color)
    item_default = fields.Boolean("Item Default?")
    manual_insert = fields.Boolean("Allow Manual Insert?")

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
        Prevent delete code of type that is used on item
        :return: SUPER
        """
        for rec in self:
            if rec.item_ids:
                raise UserError(_("It's not possible to delete item type used on active item %s "
                                  % rec.item_ids.mapped('display_name')))
        return super().unlink()

    def write(self, vals):
        """
        Prevent edit code of type that is used on item
        :param vals: edit vals
        :return: SUPER
        """
        # logging.info(blue + "=== type write vals %s" % str(vals) + reset)
        if vals.get('code'):
            for rec in self:
                if rec.item_ids:
                    # logging.info(yellow + "Related Items %s" % rec.item_ids + reset)
                    raise UserError(_("It's not possible to edit item type code used on active item %s "
                                      % rec.item_ids.mapped('display_name')))
        return super().write(vals)

    # =========== Business Methods
    def open_items(self):
        """
        open items that use this type
        :return: action view
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('stone_production.stone_item_action')
        action['domain'] = [('id', 'in', self.item_ids.ids)]
        return action

    @api.constrains('item_default')
    def _constrain_one_type_default(self):
        for rec in self:
            if isinstance(rec.id, int):
                other_ids = self.search([('item_default', '=', True)])
                if len(other_ids) > 1:
                    raise UserError(_("Can't have more than 1 default type\n %s already set as default" % other_ids.mapped('display_name')))
# Ahmed Salama Code End.

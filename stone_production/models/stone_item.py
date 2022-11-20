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
# Ahmed Salama Code Start ---->


class StoneItemType(models.Model):
    _name = 'stone.item'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Stone ITem"
    _check_company_auto = True
    _rec_names_search = ['name', 'type_id', 'code', 'parent_id']

    # ========== compute methods
    def _compute_dim_uom_name(self):
        """ Get the unit of measure to one axe dimension
        """
        product_length_in_feet_param = self.env['ir.config_parameter'].sudo().get_param('product.volume_in_cubic_feet')
        dim_foot = self.env.ref('uom.product_uom_inch')
        dim_meter = self.env.ref('uom.product_uom_cm')
        for rec in self:
            if product_length_in_feet_param == '1':
                dim_uom_id = dim_foot
            else:
                dim_uom_id = dim_meter
            rec.dimension_uom_id = dim_uom_id

    def _concat_code(self, item_type, item_source, item_color, next_num=False):
        code = "%s-%s-%s%s" % (item_type, item_source, item_color, next_num and "-%s" % next_num or '')
        return code

    # @api.depends('type_id', 'color_id', 'source_id')
    # def _compute_code(self):
    #     """
    #     Compute code of product item from type/source/color/source serial
    #     :return:
    #     """
    #     for rec in self:
    #         code = '/'
    #         # logging.info(blue + "Start Compute code of item: %s" % rec.name + reset)
    #         if rec.type_id and rec.source_id and rec.color_id:
    #             # next_num = rec.source_id.next_num + 1
    #             # code_slices = "%s-%s-%s" % (rec.type_id.code, rec.source_id.code, rec.color_id.code)
    #             # code = "%s-%s-%s-%s" % (rec.type_id.code, rec.source_id.code, rec.color_id.code, next_num)
    #             # logging.info(yellow + "next_num: %s" % next_num + reset)
    #             # logging.info(yellow + "code: %s" % code + reset)
    #             # if code and next_num:
    #             #     rec.write({'code': code, 'code_slices': code_slices})
    #             code = rec._concat_code(rec.type_id.code, rec.source_id.code, rec.color_id.code)
    #         rec.code_compute = code

    @api.depends('width', 'length', 'height', 'thickness', 'type_id.size', 'num_of_pieces')
    def _compute_size(self):
        """
        Compute size form dimension and total suze according to number of pieces
        """
        for rec in self:
            size_value = 0
            if rec.type_id.size == 'volume':
                size_value = rec.width * rec.length * rec.height / 1000000
            if rec.type_id.size == 'surface':
                size_value = rec.width * rec.length / 10000
            rec.size_value = size_value
            rec.total_size = size_value * rec.num_of_pieces

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        """
        Load Details of type and source and color from parent
        """
        for rec in self:
            rec.source_id = rec.parent_id.source_id.id
            rec.type_id = rec.parent_id.type_id.id
            rec.color_id = rec.parent_id.color_id.id
            rec.choice = rec.choice

    name = fields.Char("Item", required=True, readonly=True, states={'draft': [('readonly', False)]})
    # code_compute = fields.Char("Code CMP", default="/", compute=_compute_code)
    # code_num = fields.Char("Serial", default="0000", help="This field is used to store code_num")
    code = fields.Char("Code", default="/")
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    parent_id = fields.Many2one('stone.item', "Parent", readonly=True, states={'draft': [('readonly', False)]})
    parent_item_code = fields.Char('parent_id.code')
    type_id = fields.Many2one(comodel_name='stone.item.type', string="Type", required=True
                              , readonly=True, states={'draft': [('readonly', False)]})
    type_size = fields.Selection(related='type_id.size')
    type_size_uom_id = fields.Many2one(related='type_id.size_uom_id')
    source_id = fields.Many2one(comodel_name='stone.item.source', string="Source", required=True
                                , readonly=True, states={'draft': [('readonly', False)]})  # , domain=_get_source_domain
    color_ids = fields.Many2many(related='source_id.color_ids')
    color_id = fields.Many2one(comodel_name='stone.item.color', string="Color", required=True
                               , readonly=True, states={'draft': [('readonly', False)]})

    width = fields.Float('Width', digits='Stock Weight', readonly=True
                          , states={'draft': [('readonly', False)]})
    length = fields.Float('Length', digits='Stock Weight', readonly=True
                          , states={'draft': [('readonly', False)]})
    height = fields.Float('Height', digits='Stock Weight', readonly=True
                          , states={'draft': [('readonly', False)]})
    thickness = fields.Float('Thickness', digits='Stock Weight', readonly=True
                             , states={'draft': [('readonly', False)]})
    size_value = fields.Float("Size", digits='Stock Weight', compute=_compute_size)
    dimension_uom_id = fields.Many2one('uom.uom', string="UOM", compute=_compute_dim_uom_name)

    choice = fields.Char("Choice", required=True, readonly=True, states={'draft': [('readonly', False)]})
    num_of_pieces = fields.Float("Pieces", readonly=True, states={'draft': [('readonly', False)]})
    total_size = fields.Float("Total Size", compute=_compute_size)
    state = fields.Selection(selection=[('draft', 'Draft'), ('product', 'Product Created')],
                             string="Status", default='draft',
                             help="This is used to check the status of item\n"
                                  "* Draft: it mean it has no related product yet and can be edited\n"
                                  "* Product Created: it mean product has created and uer can't edit it anymore.")
    product_id = fields.Many2one('product.product', "Product", ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template', "Template", ondelete='cascade')

    # =========== Core Methods
    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.code:
                name = '[%s] %s' % (rec.code, name)
            result.append((rec.id, name))
        return result

    def write(self, vals):
        """
        This will be used to generate code
        :param vals: write_vals
        :return: SUPER
        """
        source_obj = self.env['stone.item.source']
        # logging.info(blue + "=== item write vals %s" % str(vals) + reset)
        if vals.get('source_id') or vals.get('color_id') or vals.get('type_id'):
            for rec in self:
                # if vals.get('code_slices') != rec.code_slices:
                    # logging.info(
                    #     yellow + "COMPARISON ==> New code:%s , old code:%s" % (vals.get('code_slices'), rec.code_slices) + reset)
                item_type = vals.get('type_id') or rec.type_id.code
                item_color = vals.get('color_id') or rec.color_id.code
                source_id = vals.get('source_id') and source_obj.browse(vals.get('source_id')) or rec.source_id
                item_source = source_id.code
                next_num = source_id.next_num
                vals['code'] = rec._concat_code(item_type, item_source, item_color, next_num)
                vals['code_num'] = next_num
                rec.source_id.write({'next_num': next_num + 1})
        return super(StoneItemType, self).write(vals)

    @api.model
    def create(self, vals):
        """
        This will be used to generate code
        :param vals: create vals
        :return: SUPER
        """
        source_obj = self.env['stone.item.source']
        type_obj = self.env['stone.item.type']
        color_obj = self.env['stone.item.color']
        # logging.info(blue + "=== item write vals %s" % str(vals) + reset)
        item_id = type_obj.browse(vals.get('type_id'))
        color_id = color_obj.browse(vals.get('color_id'))
        source_id = source_obj.browse(vals.get('source_id'))
        next_num = source_id.next_num
        vals['code'] = self._concat_code(item_id.code, source_id.code, color_id.code, source_id.next_num)
        vals['code_num'] = next_num
        item = super(StoneItemType, self).create(vals)
        item.source_id.write({'next_num': next_num+1})
        return item

    # def unlink(self):
    #     """
    #     Pervent delete not draft items
    #     :return: SUPER
    #     """
    #     for rec in self:
    #         if rec.state != 'draft':
    #             raise UserError(_("It's not possible to delete item which is not draft!!! "))
    #     return super(StoneItemType, self).unlink()

    # ========== Business methods
    def create_product(self):
        product_obj = self.env['product.product']
        quant_obj = self.env['stock.quant']
        for rec in self:
            if rec.state == 'draft':
                # TODO: add price of product from source_id.estimate_hour
                #      - If it's block the price will be source_id.estimate_hour * size_value
                #      - If it's others the price will be !!!!!!!!
                price = rec.source_id.estimate_hour * rec.size_value
                rec.product_id = product_obj.create({
                    'name': rec.name,
                    'default_code': rec.code,
                    'detailed_type': 'product',
                    'item_id': rec.id,
                    'type_id': rec.type_id.id,
                    'source_id': rec.source_id.id,
                    'color_id': rec.color_id.id,
                    'width': rec.width,
                    'length': rec.length,
                    'height': rec.height,
                    'thickness': rec.thickness,
                    'dimension_uom_id': rec.dimension_uom_id.id,
                    'volume': rec.size_value,
                    'lst_price': price,
                })
                rec.product_tmpl_id = rec.product_id.product_tmpl_id.id
                rec.state = 'product'
                # Add qty as stock for location of source with num_of_pieces
                quant_obj._update_available_quantity(rec.product_id, rec.source_id.location_id, rec.num_of_pieces)


# Ahmed Salama Code End.

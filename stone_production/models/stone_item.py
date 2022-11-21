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


class StoneItem(models.Model):
    _name = 'stone.item'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Stone ITem"
    _rec_names_search = ['name', 'item_type_id', 'code', 'parent_id']

    # ========== compute methods
    @api.model
    def default_get(self, fields):
        res = super(StoneItem, self).default_get(fields)
        if not res.get('item_type_id'):
            default_type = self.env['stone.item.type'].search([('item_default', '=', True)], limit=1)
            if default_type:
                print("default_type:: ", default_type)
                res['item_type_id'] = default_type.id
            else:
                raise UserError(_("No default item type has set!!!"))
        print("RES:: ", res)
        return res

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

    @api.depends('item_type_id', 'color_id', 'source_id')
    def _compute_code(self):
        """
        Compute code of product item from type/source/color/source serial
        :return:
        """
        for rec in self:
            code = '/'
            # logging.info(blue + "Start Compute code of item: %s" % rec.name + reset)
            if rec.item_type_id and rec.source_id and rec.color_id:
                next_num = rec.source_id.next_num

                code = rec._concat_code(rec.item_type_id.code, rec.source_id.code, rec.color_id.code, next_num)
            rec.code_compute = code

    @api.depends('width', 'length', 'height', 'thickness', 'item_type_id.size', 'num_of_pieces')
    def _compute_size(self):
        """
        Compute size form dimension and total suze according to number of pieces
        """
        for rec in self:
            size_value = 0
            if rec.item_type_id.size == 'volume':
                size_value = rec.width * rec.length * rec.height / 1000000
            if rec.item_type_id.size == 'surface':
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
            rec.item_type_id = rec.parent_id.item_type_id.id
            rec.color_id = rec.parent_id.color_id.id
            rec.choice_id = rec.choice_id

    @api.depends('job_order_ids')
    def _compute_remain_size(self):
        """
        Compute beginning size to be used on cut if it's not new or cancelled and created before
        """
        for rec in self:
            cut_size = 0
            remain_size = rec.size_value
            if rec.job_order_ids and isinstance(rec.id, int):
                job_orders = self.env['stone.job.order'].search([('item_id', '=', rec.id),
                                                                 ('cut_status', 'not in', ['new', 'cancel'])])
                cut_size = sum(c.cut_size_value for c in job_orders)
                remain_size -= cut_size
            rec.cut_size = cut_size
            rec.remain_size = remain_size

    name = fields.Char("Item Code", default='/')
    code_compute = fields.Char("Code CMP", default="/", compute=_compute_code)
    after_save = fields.Boolean("Readonly after save", default=False)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    parent_id = fields.Many2one('stone.item', "Parent")
    parent_item_code = fields.Char('parent_id.code')
    item_type_id = fields.Many2one(comodel_name='stone.item.type', string="Type", required=True)
    type_size = fields.Selection(related='item_type_id.size')
    type_size_uom_id = fields.Many2one(related='item_type_id.size_uom_id')
    source_id = fields.Many2one(comodel_name='stone.item.source', string="Source", required=True)
    color_ids = fields.Many2many(related='source_id.color_ids')
    color_id = fields.Many2one(comodel_name='stone.item.color', string="Color", required=True)
    width = fields.Integer('Width', digits='Stock Weight', readonly=True
                           , states={'draft': [('readonly', False)]})
    length = fields.Integer('Length', digits='Stock Weight', readonly=True
                            , states={'draft': [('readonly', False)]})
    height = fields.Integer('Height', digits='Stock Weight', readonly=True
                            , states={'draft': [('readonly', False)]})
    thickness = fields.Float('Thickness', digits='Stock Weight', readonly=True
                             , states={'draft': [('readonly', False)]})
    size_value = fields.Float("Size", digits='Stock Weight', compute=_compute_size)
    cut_size = fields.Float("Cut Size", digits='Stock Weight', compute=_compute_remain_size,
                            help="This field show the sum value for all job orders for this item which not new/cancel")
    remain_size = fields.Float("Remain Size", digits='Stock Weight', compute=_compute_remain_size,
                               help="This field show the remain value form "
                                    "all job orders for this item which not new/cancel")
    dimension_uom_id = fields.Many2one('uom.uom', string="UOM", compute=_compute_dim_uom_name)

    choice_id = fields.Many2one('stone.item.choice', "Choice", required=True)
    remarks = fields.Text("Remarks")
    num_of_pieces = fields.Float("Pieces", default=1)
    total_size = fields.Float("Total Size", compute=_compute_size)
    state = fields.Selection(selection=[('draft', 'Draft'), ('product', 'Product Created')],
                             string="Status", default='draft',
                             help="This is used to check the status of item\n"
                                  "* Draft: it mean it has no related product yet and can be edited\n"
                                  "* Product Created: it mean product has created and uer can't edit it anymore.")
    product_id = fields.Many2one('product.product', "Product", ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template', "Template", ondelete='cascade')
    job_order_ids = fields.One2many('stone.job.order', 'item_id', "Job Orders")

    # =========== Core Methods
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
        item_type_id = type_obj.browse(vals.get('item_type_id'))
        color_id = color_obj.browse(vals.get('color_id'))
        source_id = source_obj.browse(vals.get('source_id'))
        next_num = source_id.next_num
        vals['name'] = self._concat_code(item_type_id.code, source_id.code, color_id.code, source_id.next_num)
        vals['after_save'] = True
        item = super(StoneItem, self).create(vals)
        item.source_id.write({'next_num': next_num+1})
        return item

    # ========== Business methods
    def create_product(self):
        product_obj = self.env['product.product']
        quant_obj = self.env['stock.quant']
        for rec in self:
            if rec.state == 'draft':
                # TODO: add price of product from source_id.estimate_hour
                #      - If it's block the price will be source_id.estimate_hour * size_value
                #      - If it's others the price will be !!!!!!!!
                cost = rec.source_id.estimate_hour * rec.size_value
                rec.product_id = product_obj.create({
                    'name': rec.name,
                    'default_code': rec.name,
                    'detailed_type': 'product',
                    'item_id': rec.id,
                    'item_type_id': rec.item_type_id.id,
                    'source_id': rec.source_id.id,
                    'color_id': rec.color_id.id,
                    'width': rec.width,
                    'length': rec.length,
                    'height': rec.height,
                    'thickness': rec.thickness,
                    'dimension_uom_id': rec.dimension_uom_id.id,
                    'volume': rec.size_value,
                    'standard_price': cost,
                    'num_of_pieces': rec.num_of_pieces,
                    'uom_id': rec.type_size_uom_id.id,
                    'uom_po_id': rec.type_size_uom_id.id,
                })
                rec.product_tmpl_id = rec.product_id.product_tmpl_id.id
                rec.state = 'product'
                # Add qty as stock for location of source with num_of_pieces
                quant = quant_obj.create({'product_id': rec.product_id.id,
                                          'inventory_quantity': rec.total_size,
                                          'location_id': rec.source_id.location_id.id})
                quant.action_apply_inventory()
                # quant_obj._update_available_quantity(rec.product_id, rec.source_id.location_id, rec.total_size)

    @api.constrains('name')
    def _constrain_name(self):
        """
        Constrain Name
        """
        for rec in self:
            if isinstance(rec.id, int):
                other_ids = self.search([('name', '=', rec.name), ('id', '!=', rec.id)])
                if other_ids:
                    raise UserError(
                        _("Name Must be Unique!!!\n %s already have this name." % other_ids.mapped(
                            'display_name')))

    def open_orders(self):
        """
        open orders that use this item
        :return: action view
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('stone_production.stone_job_order_action')
        action['context'] = {'default_item_id': self.id}
        action['domain'] = [('id', 'in', self.job_order_ids.ids)]
        return action


class StoneItemChoice(models.Model):
    _name = 'stone.item.choice'
    _description = "Stone Item Choice"

    name = fields.Char("Choice")
# Ahmed Salama Code End.

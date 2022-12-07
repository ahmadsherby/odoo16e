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


class StoneItemPallet(models.Model):
    _name = 'stone.item.pallet'
    _description = "Stone Item Pallet"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _check_company_auto = True

    name = fields.Char("Pallet")
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)


class StoneItemChoice(models.Model):
    _name = 'stone.item.choice'
    _description = "Stone Item Choice"

    name = fields.Char("Choice")


class StoneItem(models.Model):
    _name = 'stone.item'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Stone ITem"
    _rec_names_search = ['name', 'item_type_id.code', 'item_type_id.name', 'code', 'parent_id.name']
    _check_company_auto = True

    # ========== compute methods
    @api.model
    def default_get(self, fields):
        res = super(StoneItem, self).default_get(fields)
        if not res.get('item_type_id'):
            default_type = self.env['stone.item.type'].search([('item_default', '=', True)], limit=1)
            if default_type:
                res['item_type_id'] = default_type.id
            else:
                raise UserError(_("No default item type has set!!!"))
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
                if rec.item_type_id == self.env.ref('stone_production.item_type_block'):
                    next_num = rec.source_id.next_num
                    code = rec._concat_code(rec.item_type_id.code, rec.source_id.code, rec.color_id.code, next_num)
                if rec.item_type_id == self.env.ref('stone_production.item_type_slab'):
                    code = "%s-%s*%s*%s" % (rec.color_id.code, rec.length, rec.width, rec.thickness)
            rec.code_compute = code

    @api.depends('width', 'length', 'height', 'thickness', 'uom_cost',
                 'item_type_id.size', 'num_of_pieces')
    def _compute_size(self):
        """
        Compute size form dimension and total size according to number of pieces
        """
        for rec in self:
            piece_size = 0
            if rec.item_type_id.size == 'volume':
                piece_size = rec.length * rec.width * rec.height / 1000000
            if rec.item_type_id.size == 'surface':
                piece_size = rec.length * rec.width / 10000
            rec.piece_size = piece_size
            piece_cost = piece_size * rec.uom_cost
            rec.piece_cost = piece_cost

            rec.total_size = piece_size * rec.num_of_pieces
            rec.item_total_cost = piece_cost * rec.num_of_pieces

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        """
        Load Details of type and source and color from parent
        """
        for rec in self:
            if rec.parent_id:
                rec.source_id = rec.parent_id.source_id.id
                rec.item_type_id = rec.parent_id.item_type_id.id
                rec.color_id = rec.parent_id.color_id.id
                rec.choice_id = rec.choice_id

    @api.depends('num_of_pieces', 'job_order_ids.num_of_pieces')
    def _compute_slab_remain_pieces(self):
        """
        This shall be effect only on Slab items
        """
        for rec in self:
            slab_remain = 0
            if rec.item_type_id == self.env.ref('stone_production.item_type_slab'):
                slab_remain = rec.num_of_pieces
                if rec.job_order_ids:
                    slab_remain = rec.num_of_pieces - sum(j.num_of_pieces for j in rec.job_order_ids.filtered(lambda jo: jo.cut_status == 'completed'))
            rec.slab_remain_num_of_pieces = slab_remain

    name = fields.Char("Item Code", default='/')
    code_compute = fields.Char("Code CMP", default="/", compute=_compute_code)
    after_save = fields.Boolean("Readonly after save", default=False)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', "Currency")
    parent_id = fields.Many2one('stone.item', "Parent")
    parent_item_code = fields.Char('parent_id.code')
    item_type_id = fields.Many2one(comodel_name='stone.item.type', string="Type", required=True)
    type_size = fields.Selection(related='item_type_id.size')
    type_size_uom_id = fields.Many2one(related='item_type_id.size_uom_id')
    type_size_uom_name = fields.Char(related='type_size_uom_id.name')
    source_id = fields.Many2one(comodel_name='stone.item.source', string="Source",
                                domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    vendor_id = fields.Many2one('res.partner', 'Source Vendor')
    color_ids = fields.Many2many(related='source_id.color_ids')
    color_id = fields.Many2one(comodel_name='stone.item.color', string="Color", required=True,
                               domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    length = fields.Integer('Length', digits='Stock Weight', readonly=True
                            , states={'draft': [('readonly', False)]})
    width = fields.Integer('Width', digits='Stock Weight', readonly=True
                           , states={'draft': [('readonly', False)]})
    height = fields.Integer('Height', digits='Stock Weight', readonly=True
                            , states={'draft': [('readonly', False)]})
    thickness = fields.Float('Thickness', digits='Stock Weight', readonly=True
                             , states={'draft': [('readonly', False)]})
    piece_size = fields.Float("Piece Size", digits='Stock Weight', compute=_compute_size)
    piece_cost = fields.Float("Piece Cost", digits='Stock Weight', compute=_compute_size)
    cut_size = fields.Float("Cut Size", digits='Stock Weight',
                            help="This field show the sum value for all job orders for this item which not new/cancel")
    remain_size = fields.Float("Remain Size", digits='Stock Weight',
                               help="This field show the remain value form "
                                    "all job orders for this item which not new/cancel")
    dimension_uom_id = fields.Many2one('uom.uom', string="UOM", compute=_compute_dim_uom_name)
    dimension_uom_name = fields.Char(related='dimension_uom_id.name')

    choice_id = fields.Many2one('stone.item.choice', "Choice", required=True)
    remarks = fields.Text("Remarks")
    num_of_pieces = fields.Float("Pieces", default=1)
    slab_remain_num_of_pieces = fields.Float("Slab Remain Pieces", compute=_compute_slab_remain_pieces,
                                             help="Slab remain pieces after cut it into items")
    uom_cost = fields.Float("UOM Cost")
    total_size = fields.Float("Item Total Size", compute=_compute_size)
    item_total_cost = fields.Float("Item Total Cost", compute=_compute_size)
    state = fields.Selection(selection=[('draft', 'Draft'), ('product', 'Product Created')],
                             string="Status", default='draft', tracking=True,
                             help="This is used to check the status of item\n"
                                  "* Draft: it mean it has no related product yet and can be edited\n"
                                  "* Product Created: it mean product has created and uer can't edit it anymore.")
    cut_status = fields.Selection(selection=[('new', 'New'), ('under_cutting', 'Under Cutting'),
                                             ('cutting_completed', 'Cutting Completed'),
                                             ('item_completed', 'Item Completed')], string="Cut Status",
                                  default='new', tracking=True,
                                  help="This is status of cut operation:\n"
                                       "* New: this is new status for job order where fields is open to edit.\n"
                                       "* Under Cutting: this is status for valid for cutting.\n"
                                       "* Cutting Completed: this is status with it's not valid to use.\n")
    product_id = fields.Many2one('product.product', "Product", ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template', "Template", ondelete='cascade')
    job_order_ids = fields.One2many('stone.job.order', 'item_id', "Job Orders")
    cut_job_order_id = fields.Many2one('stone.job.order', "Cut Job Order")
    pallet_id = fields.Many2one('stone.item.pallet', "Pallet")

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
        code = "/"
        next_num = False
        company_id = self.env.user.company_id
        if vals.get('company_id'):
            company_id = self.env['res.company'].browse(vals.get('company_id'))
        vals['currency_id'] = company_id.currency_id.id
        if not vals.get('product_id'):
            if item_type_id == self.env.ref('stone_production.item_type_block'):
                next_num = source_id.next_num
                vals['name'] = self._concat_code(item_type_id.code, source_id.code, color_id.code, source_id.next_num)
                vals['uom_cost'] = source_id.estimate_hour
            elif item_type_id in (self.env.ref('stone_production.item_type_slab'),
                                  self.env.ref('stone_production.item_type_tile'),
                                  self.env.ref('stone_production.item_type_strip')):
                thickness = vals.get('thickness') and str(vals.get('thickness')) or 1
                if '.' in thickness:
                    thickness = thickness.split('.')[0]
                code = "%s-%s*%s*%s-%s" % (color_id.code, vals.get('length'), vals.get('width'), thickness, "%s" % self.env.context.get('job_order_line') or '')
                if item_type_id == self.env.ref('stone_production.item_type_tile'):
                    code = "Tiles-%s" % code
                elif item_type_id == self.env.ref('stone_production.item_type_strip'):
                    code = "Strips-%s" % code
                vals['name'] = code
        else:
            pass  # TODO: this will be name from product if it's PO
        vals['after_save'] = True
        item = super(StoneItem, self).create(vals)
        if next_num:
            item.source_id.write({'next_num': next_num+1})
        return item

    # ========== Business methods
    def create_product(self):
        product_obj = self.env['product.product']
        quant_obj = self.env['stock.quant']
        for rec in self:
            if rec.state == 'draft':
                rec.product_id = product_obj.create({
                    'name': rec.name,
                    'default_code': rec.name,
                    'detailed_type': 'product',
                    'item_id': rec.id,
                    'categ_id': rec.item_type_id.categ_id.id,
                    'item_type_id': rec.item_type_id.id,
                    'source_id': rec.source_id.id,
                    'color_id': rec.color_id.id,
                    'width': rec.width,
                    'length': rec.length,
                    'height': rec.height,
                    'thickness': rec.thickness,
                    'stone_size_eq': rec.type_size,
                    'dimension_uom_id': rec.dimension_uom_id.id,
                    'piece_size': rec.piece_size,
                    'piece_size_uom_id': rec.type_size_uom_id.id,
                    'standard_price': rec.uom_cost,
                    'num_of_pieces': rec.num_of_pieces,
                    'uom_id': rec.type_size_uom_id.id,
                    'uom_po_id': rec.type_size_uom_id.id,
                    'choice_id': rec.choice_id.id,
                    'remarks': rec.remarks,
                    'pallet_id': rec.pallet_id and rec.pallet_id.id or False,
                    'company_id': rec.company_id and rec.company_id.id or False,
                })
                rec.product_tmpl_id = rec.product_id.product_tmpl_id.id
                # update it's remain size with cut size, cost with cost equation, and state
                rec.write({
                    'state': 'product',
                    'remain_size': rec.piece_size,
                })
                # Add qty as stock for location of source with num_of_pieces
                if rec.item_type_id == self.env.ref('stone_production.item_type_block'):
                    location_id = rec.source_id.location_id
                else:
                    location_id = self.env.company.stone_finished_good_loc_id
                    if not location_id:
                        raise UserError(_("Finished Good Location is missing on config setting for :%s Company" % self.env.company.display_name))
                quant = quant_obj.create({'product_id': rec.product_id.id,
                                          'inventory_quantity': rec.total_size,
                                          'location_id': location_id.id})
                quant.action_apply_inventory()
                # quant_obj._update_available_quantity(rec.product_id, rec.source_id.location_id, rec.total_size)

    @api.constrains('name', 'parent_id')
    def _constrain_name(self):
        """
        Constrain Name
        """
        for rec in self:
            if isinstance(rec.id, int):
                domain = [('name', '=', rec.name), ('id', '!=', rec.id)]
                if rec.parent_id:
                    domain.append(('parent_id', '=', rec.parent_id.id))
                other_ids = self.search(domain)
                if other_ids:
                    raise UserError(
                        _("Name Must be Unique!!!\n %s already have this name." % other_ids.mapped(
                            'display_name')))

    # =========== Core Methods
    @api.constrains('width', 'length')
    def _check_values(self):
        for rec in self:
            if isinstance(rec.id, int) and rec.cut_status == 'under_cutting':
                if rec.width == 0.0 or rec.length == 0.0:
                    raise UserError(_('Item Details (Length & Width) Values should not be zero.'))
            if rec.item_type_id == self.env.ref('stone_production.item_type_block') and \
                    rec.height == 0.0:
                raise UserError(_('Item Height should not be zero.'))

    def open_orders(self):
        """
        open orders that use this item
        :return: action view
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('stone_production.stone_job_order_action')
        action['context'] = {'default_item_id': self.id}
        action['domain'] = [('id', 'in', self.job_order_ids.ids)]
        if self.item_type_id == self.env.ref('stone_production.item_type_block'):
            action['views'] = [(self.env.ref('stone_production.stone_job_order_tree_view').id, 'tree'),
                               (self.env.ref('stone_production.stone_job_order_block_form_view').id, 'form')]

        elif self.item_type_id == self.env.ref('stone_production.item_type_slab'):
            action['views'] = [(self.env.ref('stone_production.stone_job_order_tree_view').id, 'tree'),
                               (self.env.ref('stone_production.stone_job_order_slab_form_view').id, 'form')]

        return action

    def action_block_cut(self):
        job_order_obj = self.env['stone.job.order']
        for rec in self:
            job_order_id = job_order_obj.create({
                'job_type_id': self.env.ref('stone_production.stone_job_order_type_cutting_block').id,
                'job_type': 'block',
                'job_machine_id': self.env.ref('stone_production.stone_job_order_machine_cutting_block').id,
                'color_id': rec.color_id.id,
                'choice_id': rec.choice_id.id,
                'currency_id': rec.currency_id and rec.currency_id.id or False,
                'item_id': rec.id,
                'width': rec.width,
                'length': rec.length,
                'height': rec.height,
                'thickness': rec.thickness,
                'item_size': rec.piece_size,
                'remain_size': rec.remain_size,
                'remarks': rec.remarks,
                'main_item_cost': rec.item_total_cost,
                'piece_cost': rec.piece_cost,
                'cut_status': 'under_cutting',
            })
            rec.cut_status = 'under_cutting'
            compose_form = self.env.ref('stone_production.stone_job_order_block_form_view', False)
            return {
                'name': 'Block Cutting',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stone.job.order',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'res_id': job_order_id.id,
            }

    def action_slab_cut(self):
        job_order_obj = self.env['stone.job.order']
        for rec in self:
            job_order_id = job_order_obj.create({
                'job_type_id': self.env.ref('stone_production.stone_job_order_type_cutting_slab').id,
                'job_type': 'slab',
                'job_machine_id': self.env.ref('stone_production.stone_job_order_machine_cutting_slab').id,
                'parent_id': rec.cut_job_order_id.id,
                'color_id': rec.color_id.id,
                'choice_id': rec.choice_id.id,
                'item_id': rec.id,
                'width': rec.width,
                'length': rec.length,
                'height': rec.height,
                'thickness': rec.thickness,
                'num_of_pieces': rec.slab_remain_num_of_pieces,
                'slab_num_of_pieces': rec.num_of_pieces,
                'item_size': rec.total_size,
                'remain_size': rec.remain_size,
                'remarks': rec.remarks,
                'main_item_cost': rec.item_total_cost,
                'piece_cost': rec.piece_cost,
                'job_order_status': 'under_converting',
                'cut_status': 'under_cutting',
            })
            rec.cut_status = 'under_cutting'
            compose_form = self.env.ref('stone_production.stone_job_order_slab_form_view', False)
            return {
                'name': 'Block Cutting',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stone.job.order',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'res_id': job_order_id.id,
            }

    def action_item_completed(self):
        for rec in self:
            rec.cut_status = 'item_completed'
# Ahmed Salama Code End.

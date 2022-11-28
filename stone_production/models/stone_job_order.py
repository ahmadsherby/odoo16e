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
job_order_types = [('block', 'Cutting Blocks'),
                   ('slab', 'Cutting Slabs')]


class StoneJobOrderType(models.Model):
    _name = 'stone.job.order.type'
    _description = "Stone Job Type"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    name = fields.Char("Job Type")
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    item_type_id = fields.Many2one(comodel_name='stone.item.type',
                                   string="Item Type", required=True)
    job_order_ids = fields.One2many('stone.job.order', 'job_type_id', "Job Orders")

    # =========== Core Methods
    def unlink(self):
        """
        Prevent delete code of type that is used on order
        :return: SUPER
        """
        for rec in self:
            if rec.job_order_ids:
                raise UserError(_("It's not possible to delete job type used on active job orders %s "
                                  % rec.job_order_ids.mapped('display_name')))
        return super().unlink()

    # =========== Business Methods
    def open_orders(self):
        """
        open orders that use this type
        :return: action view
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('stone_production.stone_job_order_action')
        action['context'] = {'default_job_type_id': self.id}
        action['domain'] = [('id', 'in', self.job_order_ids.ids)]
        action['views'] = [(self.env.ref('stone_production.stone_job_order_tree_view').id, 'tree'),
                           (self.env.ref('stone_production.stone_job_order_slab_form_view').id, 'form')]
        return action


class StoneJobOrderMachine(models.Model):
    _name = 'stone.job.order.machine'
    _description = "Stone Job Machine"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    name = fields.Char("Job Machine")
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    item_type_id = fields.Many2one(comodel_name='stone.item.type',
                                   string="Item Type", required=True)
    job_order_ids = fields.One2many('stone.job.order', 'job_type_id', "Job Orders")

    # =========== Core Methods
    def unlink(self):
        """
        Prevent delete machine that is used on order
        :return: SUPER
        """
        for rec in self:
            if rec.job_order_ids:
                raise UserError(_("It's not possible to delete job type used on active job orders %s "
                                  % rec.job_order_ids.mapped('display_name')))
        return super().unlink()

    # =========== Business Methods
    def open_orders(self):
        """
        open orders that use this machine
        :return: action view
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('stone_production.stone_job_order_action')
        action['context'] = {'default_job_machine_id': self.id}
        action['domain'] = [('id', 'in', self.job_order_ids.ids)]
        return action


class StoneJobOrder(models.Model):
    _name = 'stone.job.order'
    _description = "Stone Job Order"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    # _rec_names_search = ['name', 'item_id', 'item_type_id', 'parent_id']

    # ========== compute methods
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if res.get('job_type'):
            default_type = self.env.ref('stone_production.stone_job_order_type_cutting_%s' % res.get('job_type'))
            if default_type:
                res['job_type_id'] = default_type.id
        return res

    @api.depends('cut_width', 'cut_length', 'cut_height', 'cut_thickness', 'line_ids.conv_total_size',
                 'item_type_id.size', 'cut_num_of_pieces', 'item_size', 'main_item_cost', 'num_of_pieces')
    def _compute_cut_size(self):
        """
        Compute size form dimension and total suze according to number of pieces
        """
        for rec in self:
            piece_cut_size_value = 0
            cut_num_of_pieces = rec.cut_num_of_pieces
            if rec.job_type_id == self.env.ref('stone_production.stone_job_order_type_cutting_block'):
                if rec.item_type_id.size == 'volume':
                    piece_cut_size_value = rec.cut_length * rec.cut_width * rec.cut_height / 1000000
                if rec.item_type_id.size == 'surface':
                    piece_cut_size_value = rec.cut_length * rec.cut_width / 10000
                cut_num_of_pieces = rec.cut_num_of_pieces
            elif rec.job_type_id == self.env.ref('stone_production.stone_job_order_type_cutting_slab'):
                if rec.item_type_id.size == 'volume':
                    piece_cut_size_value = rec.length * rec.width * rec.height / 1000000
                if rec.item_type_id.size == 'surface':
                    piece_cut_size_value = rec.length * rec.width / 10000
                cut_num_of_pieces = rec.num_of_pieces
            rec.cut_size_value = piece_cut_size_value
            rec.cut_total_cost = rec.item_size and \
                                 piece_cut_size_value * cut_num_of_pieces * (rec.main_item_cost / rec.item_size) or 0
            rec.cut_total_size_for_line_ids = sum(i.conv_total_size for i in rec.line_ids) if rec.line_ids else 0
            line_ids_uom_cost = rec.cut_total_cost / rec.cut_total_size_for_line_ids if rec.cut_total_size_for_line_ids else 0
            rec.line_ids_uom_cost = line_ids_uom_cost
            for line in rec.line_ids:
                line.write({
                    'line_ids_uom_cost': line_ids_uom_cost,
                    'conv_cost': line_ids_uom_cost * line.conv_total_size
                })

    @api.depends('num_of_pieces', 'slab_num_of_pieces')
    def _compute_slab_pieces(self):
        """
        Compute remain slab only for slab job orders
        """
        for rec in self:
            rec.slab_remain_num_of_pieces = rec.slab_num_of_pieces - rec.num_of_pieces

    name = fields.Char("Job Order", default="/", required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one('res.currency', "Currency")
    currency_name = fields.Char(related='currency_id.name')
    job_type_id = fields.Many2one('stone.job.order.type', "Job Type")
    item_type_id = fields.Many2one(related='job_type_id.item_type_id')
    job_type = fields.Selection(job_order_types, "Job Type", required=True)
    job_machine_id = fields.Many2one('stone.job.order.machine', "Job Machine", required=True)
    item_id = fields.Many2one('stone.item', "Item", required=True)
    item_type_size = fields.Selection(related='job_type_id.item_type_id.size')
    type_size_uom_id = fields.Many2one(related='job_type_id.item_type_id.size_uom_id',
                                       help="UOM of size to be used on current size")
    type_size_uom_name = fields.Char(related='type_size_uom_id.name')
    item_size_uom_id = fields.Many2one(related='item_id.item_type_id.size_uom_id',
                                       help="UOM of size of item to be used on remaining")
    item_size_uom_name = fields.Char(related='item_size_uom_id.name')

    dimension_uom_id = fields.Many2one(related='item_id.dimension_uom_id',
                                       help="UOM of one dimension")
    dimension_uom_name = fields.Char(related='dimension_uom_id.name')
    parent_id = fields.Many2one('stone.job.order', "Parent")
    # Auto Filling Fields
    length = fields.Integer('Length', digits='Stock Weight', readonly=True)
    width = fields.Integer('Width', digits='Stock Weight', readonly=True)
    height = fields.Integer('Height', digits='Stock Weight', readonly=True)
    thickness = fields.Float('Thickness', digits='Stock Weight', readonly=True)
    item_size = fields.Float("Item Size", digits='Stock Weight', readonly=True)
    remain_size = fields.Float("Remain Size", digits='Stock Weight', readonly=1)
    num_of_pieces = fields.Float("Pieces", default=1, help="Used number of pieces on this job order")
    slab_num_of_pieces = fields.Float("Slab Pieces", default=1, help="Slab total number of pieces")
    slab_remain_num_of_pieces = fields.Float("Slab Remain Pieces", default=1,
                                             compute=_compute_slab_pieces,
                                             help="Slab remain pieces after cut it into items")
    color_id = fields.Many2one(comodel_name='stone.item.color', string="Color", readonly=True)
    choice_id = fields.Many2one('stone.item.choice', "Choice")
    remarks = fields.Text("Remarks")
    main_item_cost = fields.Float("Job Order Cost(Main Item)")
    piece_cost = fields.Float("Piece Cost")

    # User Filling Fields
    cut_length = fields.Integer('Cut Length', digits='Stock Weight')
    cut_width = fields.Integer('Cut Width', digits='Stock Weight')
    cut_height = fields.Integer('Cut Height', digits='Stock Weight')
    cut_thickness = fields.Float('Cut Thickness', digits='Stock Weight')
    cut_size_value = fields.Float("Cut Size", digits='Stock Weight', compute=_compute_cut_size)
    cut_num_of_pieces = fields.Float("Pieces", default=1)
    cut_total_cost = fields.Float("Cut Total Cost")

    cut_status = fields.Selection(selection=[('new', 'New'), ('under_cutting', 'Under Cutting'),
                                             ('completed', 'Completed'), ('cancel', 'Cancelled')],
                                  string="Cutting Status", default='new', tracking=True,
                                  help="This is status of cutting operation:\n"
                                       "* New: this is new status for job order where fields is open to edit.\n"
                                       "* Under Cutting: this is status for valid for cutting.\n"
                                       "* Completed: this is status done jobs which not valid to use.\n")
    job_order_status = fields.Selection(selection=[('new', 'New'), ('under_converting', 'Under Converting'),
                                                   ('job_completed', 'Job Order Completed'),
                                                   ('cancel', 'Cancelled')],
                                        string="Job Order Status", default='new', tracking=True,
                                        help="This is status of converting:\n"
                                             "* New: this is new status for job order where fit's ready to start convert it.\n"
                                             "* Under Converting: this is status for valid for converting.\n"
                                             "* Job Order Completed: this is status done jobs which is not valid to re-use.\n")
    cut_item_ids = fields.One2many(comodel_name='stone.item', inverse_name='cut_job_order_id', string="Cut Items")
    line_ids = fields.One2many('stone.job.order.line', 'job_order_id', "Convert Lines")
    cut_total_size_for_line_ids = fields.Float("Total Size for All lines", compute=_compute_cut_size)
    line_ids_uom_cost = fields.Float("Line UOM Cost", compute=_compute_cut_size)

    # =========== Core Methods
    @api.model
    def create(self, vals):
        # Todo comment from Sherby: you need to check that no created JO for the same
        # Todo: block in any status rather than completed
        """
        This will be used to generate code
        :param vals: create vals
        :return: SUPER
        """
        vals['name'] = self.env['ir.sequence'].next_by_code('stone.job.order')
        return super().create(vals)

    def unlink(self):
        """
        Prevent delete not new/cancel items
        :return: SUPER
        """
        for rec in self:
            if rec.cut_status not in ('cancel'):
                raise UserError(_("It's not possible to delete job order which is cut status not in cancel!!! "))
        return super().unlink()

    @api.constrains('cut_width', 'cut_length', 'cut_height')
    def _check_values(self):
        for rec in self:
            if isinstance(rec.id, int) and rec.cut_status == 'under_cutting':
                if rec.cut_width == 0.0 or rec.cut_length == 0.0:
                    raise UserError(_('Job Order Cut Details (Length & Width) Values should not be zero.'))
                if rec.job_type_id == self.env.ref('stone_production.stone_job_order_type_cutting_block') and \
                        rec.cut_height == 0.0:
                    raise UserError(_('Job Order Cut Height should not be zero.'))

    @api.constrains('num_of_pieces', 'slab_num_of_pieces')
    def _constrain_slab_pieces(self):
        """
        Constrain on slab job order to avoid set number of pieces l=more than the avaliable
        """
        for rec in self:
            if rec.job_type_id == self.env.ref('stone_production.stone_job_order_type_cutting_slab'):
                if rec.num_of_pieces > rec.slab_num_of_pieces:
                    raise UserError(_("The Used pieces %s can't be more than the slab total pieces %s"
                                      % (rec.num_of_pieces, rec.slab_num_of_pieces)))
                if rec.num_of_pieces <= 0:
                    raise UserError(_("The Used pieces can't be less or equal zero!!!"))

    # ========== Business methods
    # The Next action if response on create job order itself
    # ================================================
    def action_start_cutting_job_order(self):
        """
        This action is to set job order ready to be cut itself
        """
        for rec in self:
            rec.item_id.cut_status = 'under_cutting'
            rec.cut_status = 'under_cutting'

    def action_done_cutting_job_order(self):
        """
        This action is to set job order done cutting and ready to be converted
        """
        for rec in self:
            rec.cut_status = 'completed'
            item_remain_size = rec.item_id.remain_size - rec.cut_size_value
            rec.item_id.write({
                'cut_status': 'cutting_completed',
                'cut_size': rec.item_id.cut_size + rec.cut_size_value,
                'remain_size': item_remain_size
            })
            # update it's remain size with cut size
            rec.remain_size = item_remain_size

    def action_cancel(self):
        for rec in self:
            rec.cut_status = 'cancel'
            rec.job_order_status = 'cancel'

    # The Next action if response on convert job order
    # ================================================
    def action_start_convert_job_order(self):
        """
        This action is to set job order ready to be cute which remove if from valid to convert results
        """
        for rec in self:
            write_vals = {'job_order_status': 'under_converting'}
            rec.write(write_vals)

    def action_create_converted(self):
        """
        Convert Exist lines into items
        """
        stone_item_obj = self.env['stone.item']
        if not self.line_ids:
            raise UserError(_("IT's Mandatory to have Converted lines to be convert!!!"))
        for rec in self.line_ids:
            stone_item_obj.with_context(job_order_line=rec.id).create({
                'cut_job_order_id': self.id,
                'parent_id': self.item_id.id,
                'choice_id': self.choice_id.id,
                'source_id': self.item_id.source_id.id,
                'color_id': self.item_id.color_id.id,
                'remarks': self.remarks,
                'item_type_id': rec.conv_type_id.id,
                'width': rec.conv_width,
                'length': rec.conv_length,
                'height': rec.conv_height,
                'thickness': rec.conv_thickness,
                'num_of_pieces': rec.conv_num_of_pieces,
                'remain_size': rec.conv_size_value,
                'uom_cost': rec.line_ids_uom_cost,
                'pallet_id': rec.pallet_id and rec.pallet_id.id or False,
            })
        write_vals = {'job_order_status': 'job_completed'}
        # in case of slab
        if self.job_type_id == self.env.ref('stone_production.stone_job_order_type_cutting_slab')\
                and self.slab_remain_num_of_pieces == 0.0:
            write_vals['cut_status'] = 'completed'
        self.write(write_vals)
        action = self.env["ir.actions.actions"]._for_xml_id('stone_production.stone_item_action')
        action['domain'] = [('cut_job_order_id', '=', self.id)]
        return action

    def action_open_items(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('stone_production.stone_item_action')
        action['context'] = {'default_cut_job_order_id': self.id}
        action['domain'] = [('cut_job_order_id', '=', self.id)]
        return action


class StoneJobOrderLine(models.Model):
    _name = 'stone.job.order.line'
    _description = "Stone Job Order Line"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _rec_name = 'job_order_id'

    # ========== compute methods
    @api.depends('conv_width', 'conv_length', 'conv_num_of_pieces',
                 'conv_type_id.size')
    def _compute_conv_size(self):
        """
        Compute Convert size dimension and total size according to number of pieces
        """
        for rec in self:

            conv_size_value = main_item_cost = conv_total_size_for_all_job_order_lines = 0
            if rec.conv_type_id.size == 'volume':
                conv_size_value = rec.conv_length * rec.conv_width * rec.conv_height / 1000000
            if rec.conv_type_id.size == 'surface':
                conv_size_value = rec.conv_length * rec.conv_width / 10000
            rec.conv_size_value = conv_size_value
            rec.conv_total_size = conv_size_value * rec.conv_num_of_pieces
            # logging.info(red + "1 %s" % rec.conv_total_size + reset)
            # uom_cost = rec.job_order_id.line_ids_uom_cost
            # logging.info(blue + "line_ids_uom_cost :%s" % uom_cost + reset)
            # conv_cost = 0
            # if rec.conv_total_size:
            #     conv_cost = uom_cost * rec.conv_total_size
            # logging.info(green + "conv_cost: %s" % conv_cost + reset)
            # rec.conv_cost = conv_cost
            # rec.line_ids_uom_cost = uom_cost

    # =========== Core Methods
    @api.constrains('conv_width', 'conv_length')
    def _check_values(self):
        for rec in self:
            if isinstance(rec.id, int):
                if rec.conv_width == 0.0 or rec.conv_length == 0.0:
                    raise UserError(_('Convert Item (Length & Width) Values should not be zero.'))

    job_order_id = fields.Many2one('stone.job.order', "Job Order")
    conv_type_id = fields.Many2one('stone.item.type', "Item Type", required=True,  readonly=True
                                   , states={'draft': [('readonly', False)]})
    conv_type_size = fields.Selection(related='conv_type_id.size',
                                      help="The Equation of ")
    conv_size_uom_id = fields.Many2one(related='conv_type_id.size_uom_id',
                                       help="UOM of size of item to be used on remaining")
    conv_length = fields.Integer('Length', digits='Stock Weight', readonly=True
                                 , states={'draft': [('readonly', False)]})
    conv_width = fields.Integer('Width', digits='Stock Weight', readonly=True
                                , states={'draft': [('readonly', False)]})
    conv_height = fields.Integer('Height', digits='Stock Weight', readonly=True
                                 , states={'draft': [('readonly', False)]})
    conv_thickness = fields.Float('Thickness', digits='Stock Weight', readonly=True
                                  , states={'draft': [('readonly', False)]})
    conv_size_value = fields.Float("Size", digits='Stock Weight', compute=_compute_conv_size)
    conv_num_of_pieces = fields.Float("Pieces", default=1, readonly=True
                                      , states={'draft': [('readonly', False)]})
    conv_total_size = fields.Float("Total Size", compute=_compute_conv_size)
    line_ids_uom_cost = fields.Float("UOM Cost")
    conv_cost = fields.Float("Total Cost")
    state = fields.Selection(selection=[('draft', 'Draft'), ('item', 'Item Created')],
                             string="Status", default='draft', tracking=True,
                             help="This is used to check the status of item\n"
                                  "* Draft: it mean it has no related item yet and can be edited\n"
                                  "* Item Created: it mean item has created and uer can't edit it anymore.")
    pallet_id = fields.Many2one('stone.item.pallet', "Pallet")


class StoneItemPallet(models.Model):
    _name = 'stone.item.pallet'
    _description = "Stone Item Pallet"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    name = fields.Char("Pallet")
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')


# Ahmed Salama Code End.

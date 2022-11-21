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
    _rec_names_search = ['name', 'item_id', 'item_type_id', 'parent_id']
    _rec_name = 'item_id'

    # ========== compute methods
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if res.get('job_type'):
            default_type = self.env.ref('stone_production.stone_job_order_type_cutting_%s' % res.get('job_type'))
            if default_type:
                res['job_type_id'] = default_type.id
        return res

    @api.onchange('item_id')
    def _get_beginning_size(self):
        """
        Compute beginning size to be used on cut if it's not new or cancelled and created before
        """
        for rec in self:
            beginning_size = 0
            if rec.item_id and isinstance(rec.id, int):
                before_job_order = self.env['stone.job.order'].search([('item_id', '=', rec.item_id.id),
                                                                       ('id', '<', rec.id),
                                                                       ('cut_status', 'not in', ['new', 'cancel'])])
                before_cut_size = sum(c.cut_size_value for c in before_job_order)
                beginning_size = rec.item_id.size_value - before_cut_size
            rec.beginning_size = beginning_size

    @api.depends('cut_width', 'cut_length', 'cut_height', 'cut_thickness',
                 'item_type_id.size', 'beginning_size')
    def _compute_cut_size(self):
        """
        Compute size form dimension and total suze according to number of pieces
        """
        for rec in self:
            cut_size_value = 0
            if rec.item_type_id.size == 'volume':
                cut_size_value = rec.cut_width * rec.cut_length * rec.cut_height / 1000000
            if rec.item_type_id.size == 'surface':
                cut_size_value = rec.cut_width * rec.cut_length / 10000
            rec.cut_size_value = cut_size_value
            rec.remain_size = rec.beginning_size - cut_size_value

    @api.depends('job_width', 'job_length', 'job_height', 'job_thickness', 'item_type_id.size')
    def _compute_job_size(self):
        """
        Compute size form dimension and total suze according to number of pieces
        """
        for rec in self:
            job_size_value = 0
            if rec.item_type_id.size == 'volume':
                job_size_value = rec.job_width * rec.job_length * rec.job_height / 1000000
            if rec.item_type_id.size == 'surface':
                job_size_value = rec.job_width * rec.job_length / 10000
            rec.job_size_value = job_size_value

    name = fields.Char("Job Order", default="/", required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    job_type_id = fields.Many2one('stone.job.order.type', "Job Type")
    item_type_id = fields.Many2one(related='job_type_id.item_type_id')
    job_type = fields.Selection(job_order_types, "Job Type", required=True)
    job_machine_id = fields.Many2one('stone.job.order.machine', "Job Machine")
    item_id = fields.Many2one('stone.item', "Item", required=True)
    item_type_size = fields.Selection(related='item_id.item_type_id.size')
    type_size_uom_id = fields.Many2one(related='item_id.item_type_id.size_uom_id')
    dimension_uom_id = fields.Many2one(related='item_id.dimension_uom_id')

    parent_id = fields.Many2one('stone.job.order', "Parent")

    cut_width = fields.Integer('Cut Width', digits='Stock Weight')
    cut_length = fields.Integer('Cut Length', digits='Stock Weight')
    cut_height = fields.Integer('Cut Height', digits='Stock Weight')
    cut_thickness = fields.Float('Cut Thickness', digits='Stock Weight')
    cut_size_value = fields.Float("Cut Size", digits='Stock Weight', compute=_compute_cut_size)
    beginning_size = fields.Float("Beginning Size",
                                  digits='Stock Weight', compute=_get_beginning_size)
    remain_size = fields.Float("Remain Size", digits='Stock Weight', compute=_compute_cut_size, store=True)

    cut_status = fields.Selection(selection=[('new', 'New'), ('under_cutting', 'Under Cutting'),
                                             ('completed', 'Completed'), ('cancel', 'Cancelled')],
                                  string="Cut Status", default='new',
                                  help="This is status of cut operation:\n"
                                       "* New: this is new status for job order where fields is open to edit.\n"
                                       "* Under Cutting: this is status for valid for cutting.\n"
                                       "* Completed: this is status done jobs which not valid to use.\n")

    job_width = fields.Integer('Job Width', digits='Stock Weight')
    job_length = fields.Integer('Job Length', digits='Stock Weight')
    job_height = fields.Integer('Job Height', digits='Stock Weight')
    job_thickness = fields.Float('Job Thickness', digits='Stock Weight')
    job_size_value = fields.Float("Job Size", digits='Stock Weight', compute=_compute_job_size)

    # =========== Core Methods
    @api.model
    def create(self, vals):
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
            if rec.cut_state not in ('new', 'cancel'):
                raise UserError(_("It's not possible to delete job order which is cut status not in new/cancel!!! "))
        return super().unlink()

    # ========== Business methods
    def start_cutting(self):
        for rec in self:
            rec.cut_status = 'under_cutting'
# Ahmed Salama Code End.

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


class StoneJobOrder(models.Model):
    _name = 'stone.job.order'
    _description = "Stone Job Order"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _rec_names_search = ['item_id', 'type_id', 'parent_id']
    _rec_name = 'item_id'

    # ========== compute methods
    @api.depends('cut_width', 'cut_length', 'cut_height', 'cut_thickness', 'item_type_id.size')
    def _compute_size(self):
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

    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    job_type_id = fields.Many2one('stone.job.order.type', "Job Type")
    job_type = fields.Selection(job_order_types, "Job Type", required=True)
    item_id = fields.Many2one('stone.item', "Item", required=True)
    item_type_id = fields.Many2one(related='item_id.type_id')
    item_type_size = fields.Selection(related='item_id.type_id.size')
    type_size_uom_id = fields.Many2one(related='item_id.type_id.size_uom_id')
    dimension_uom_id = fields.Many2one(related='item_id.dimension_uom_id')

    parent_id = fields.Many2one('stone.job.order', "Parent")

    cut_width = fields.Integer('Cut Width', digits='Stock Weight')
    cut_length = fields.Integer('Cut Length', digits='Stock Weight')
    cut_height = fields.Integer('Cut Height', digits='Stock Weight')
    cut_thickness = fields.Float('Cut Thickness', digits='Stock Weight')
    cut_size_value = fields.Float("Cut Size", digits='Stock Weight', compute=_compute_size)

    cut_status = fields.Selection(selection=[('new', 'New'), ('under_cutting', 'Under Cutting'),
                                             ('completed', 'Completed')], string="Cut Status", default='new',
                                  help="This is status of cut operation:\n"
                                       "* New: this is new status for job order where fields is open to edit.\n"
                                       "* Under Cutting: this is status for valid for cutting.\n"
                                       "* Completed: this is status done jobs which not valid to use.\n")
# Ahmed Salama Code End.

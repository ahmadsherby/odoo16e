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
READONLY_STATES = {
    'purchase': [('readonly', True)],
    'done': [('readonly', True)],
    'cancel': [('readonly', True)],
}


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    @api.depends('stone_production_product_ids')
    def _stone_production_product_count(self):
        for po in self:
            po.stone_production_product_count = len(po.stone_production_product_ids)

    @api.depends('landed_cost_bill_ids')
    def _landed_cost_count(self):
        for po in self:
            po.landed_cost_bill_count = len(po.landed_cost_bill_ids)

    partner_id = fields.Many2one(domain="['|', ('company_id', '=', False), ('company_id', '=', company_id),('supplier_rank','>', 0)]")
    transporter_id = fields.Many2one('res.partner', string='Transporter',
                                     states=READONLY_STATES, change_default=True, tracking=True,
                                     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('is_transporter','=', True)]",
                                     help="You can find a transporter by its Name, TIN, Email or Internal Reference, with Transporting flag.")
    tons_trans_cost = fields.Float(related='transporter_id.tons_trans_cost')
    trans_multi_factor = fields.Float(related='transporter_id.trans_multi_factor')

    stone_production_product_ids = fields.One2many('product.template', 'generated_po_id', "New Products",
                                                   states=READONLY_STATES,)
    landed_cost_bill_ids = fields.One2many('account.move', 'landed_cost_po_id', "Landed Cost Bills",)
    landed_cost_bill_count = fields.Integer(compute=_landed_cost_count)
    stone_production_product_count = fields.Integer(compute=_stone_production_product_count)
    stone_purchase_type = fields.Selection([('regular', "Regular"), ('local', "Block Local Purchase"),
                                            ('external', "External Purchase")], "Stone Purchase Type",
                                           required=True, default='regular', states=READONLY_STATES,)
    trans_bill_id = fields.Many2one('account.move', "Transportation Bill",
                                             help="Transportation created by default with validate of Block internal Purchase")
    trans_landed_cost_id = fields.Many2one('stock.landed.cost', "Transportation Landed Cost",
                                             help="Transportation Landed Cost created by default with validate of Block internal Purchase")

    # ========== Business methods
    def open_po_new_products(self):
        """
        open new products created on this po
        :return: action view
        """
        self.ensure_one()
        domain = [('purchase_source', '=', True)]
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        default_cageg_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'stone_production.stone_po_prod_categ_id'))
        if not default_cageg_id:
            raise UserError(
                _("PO. New Product Category is missing on config setting"))
        default_item_type_id = False
        if self.stone_purchase_type == 'local':
            default_item_type_id = self.env.ref('stone_production.item_type_block')
        default_source = self.env['stone.item.source'].search(domain, limit=1)
        action = self.env["ir.actions.actions"]._for_xml_id('stone_production.stone_production_new_product_action')
        ctx = {'default_generated_po_id': self.id, 'default_purchase_ok': True,
                             'default_company_id': self.company_id and self.company_id.id or False,
                             'default_item_vendor_id': self.partner_id and self.partner_id.id or False,
                             'default_source_id': default_source and default_source.id or False,
                             'default_categ_id': default_cageg_id,
                             'default_detailed_type': 'product'}
        if default_item_type_id:
            ctx['default_item_type_id'] = default_item_type_id.id
            ctx['default_uom_id'] = default_item_type_id.size_uom_id.id
            ctx['default_uom_po_id'] = default_item_type_id.size_uom_id.id
            ctx['default_piece_size_uom_id'] = default_item_type_id.size_uom_id.id
        action['context'] = ctx
        print("CTX: ", action['context'])
        action['domain'] = [('id', 'in', self.stone_production_product_ids.ids)]
        return action

    def _create_picking(self):
        super()._create_picking()
        for order in self:
            if any(pol.item_type_id for pol in order.order_line):
                # This order Contain products related to stone production
                # Todo: set done as reserve to prevent user from change done_qty
                order.picking_ids.action_set_quantities_to_reservation()

    def action_add_landed_cost(self):
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # choose the view_mode accordingly
        invoices = self.landed_cost_bill_ids
        action['domain'] = [('id', 'in', invoices.ids)]
        action['context'] = {'default_company_id': self.company_id and self.company_id.id or False,
                             'default_landed_cost_po_id': self.id,
                             'default_landed_cost_picking_ids': self.picking_ids.ids,
                             'default_move_type': 'in_invoice'}
        return action

    def action_generate_product_lines(self):
        lines = []
        for product in self.stone_production_product_ids:
            lines.append((0, 0, {
                'product_id': product.id,
                'state': 'draft',
                'partner_id': self.partner_id.id,
                'order_id': self.id
            }))
        self.order_line = [(5, 0)]
        self.order_line = lines
        self.order_line._compute_total_transport_weight()

    def button_confirm(self):
        """
        Append action on validate po
        """
        super().button_confirm()
        for order in self:
            if order.stone_purchase_type == 'local' and order.transporter_id:
                journal_id = order._get_po_journal()
                order._create_transportation_bill(journal_id)

    def _get_po_journal(self):
        # Find Default Journal
        company_id = (self.company_id or self.env.company).id
        domain = [('company_id', '=', company_id), ('type', '=', 'purchase')]
        currency_id = self.currency_id.id or self._context.get('default_currency_id')
        if currency_id and currency_id != self.company_id.currency_id.id:
            currency_domain = domain + [('currency_id', '=', currency_id)]
            journal = self.env['account.journal'].search(currency_domain, limit=1)
        else:
            journal = self.env['account.journal'].search(domain, limit=1)

        return journal

    def _create_transportation_bill(self, journal_id):
        """
        Create Transportation bill & landed cost
        :param journal_id:
        """
        bill_obj = self.env['account.move']
        trans_prod_id = self.env['product.product'].browse(int(self.env['ir.config_parameter'].sudo().get_param(
            'stone_production.stone_po_trans_prod_id')))
        if not trans_prod_id:
            raise UserError(_("Missing PO default Transportation product, please check Stone Production configurations!!!!"))
        lines = self._prepare_transportation_bill_lines(trans_prod_id)
        # Create Transportation Bill and confirm it
        self.trans_bill_id = bill_obj.create({
            'partner_id': self.transporter_id.id,
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.today(),
            'date': fields.Date.today(),
            'ref': self.name,
            'journal_id': journal_id.id,
            'landed_cost_po_id': self.id,
            'landed_cost_picking_ids': self.picking_ids.ids,
            'invoice_line_ids': lines
        })
        self.trans_bill_id.action_post()
        # Create Transportation Landed Cost And Compute It
        self.trans_landed_cost_id = self.trans_bill_id._prepare_landed_costs()
        self.trans_landed_cost_id.compute_landed_cost()

    def _prepare_transportation_bill_lines(self, trans_prod_id):
        """
        Prepare bill with pol details
        :param trans_prod_id:
        :return:
        """
        lines = []
        for line in self.order_line:
            lines.append((0, 0, {
                'product_id': trans_prod_id.id,
                'name': line.product_id.display_name,
                'is_landed_costs_line': True,
                'account_id': line.product_id.product_tmpl_id.get_product_accounts()['expense'].id,
                'quantity': line.total_trans_weight,
                'price_unit': self.transporter_id.tons_trans_cost
            }))
        return lines


class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id', 'num_of_pieces', 'piece_size')
    def onchange_product_id(self):
        super().onchange_product_id()

    @api.depends('product_packaging_qty', 'num_of_pieces', 'piece_size')
    def _compute_product_qty(self):
        super()._compute_product_qty()
        for line in self:
            if line.product_id and line.product_id.item_type_id and line.state != 'done':
                line.product_qty = line.piece_size * line.num_of_pieces

    def _suggest_quantity(self):
        """
        Append Qty needed to work regarding new product lines
        """
        print("num_of_pieces: ", self.num_of_pieces)
        super()._suggest_quantity()
        if self.product_id and self.product_id.item_type_id:
            self.product_qty = self.piece_size * self.num_of_pieces

    @api.depends('product_qty', 'product_uom', 'product_id.item_total_cost')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if not line.product_id or line.invoice_lines:
                continue
            line.price_unit = line.product_id.standard_price
        super()._compute_price_unit_and_date_planned_and_name()

    @api.onchange('item_type_id', 'order_id')
    @api.depends('item_type_id', 'order_id.stone_production_product_ids')
    def _get_product_domain(self):
        """
        Get Domain or products depend on value of New Products Field
        :return: Valid Ids
        """
        domain = []
        if self.order_id.company_id:
            domain = ['|', ('company_id', '=', False), ('company_id', '=', self.order_id.company_id.id)]
        if self.order_id.stone_production_product_ids:
            domain.append(('id', 'in', self.order_id._origin.stone_production_product_ids.mapped('product_variant_id.id')))
        else:
            domain.append(('purchase_ok', '=', True))
            domain.append(('item_type_id', '=', False))
        product_ids = self.env['product.product'].search(domain).ids
        return {'domain': {'product_id': [('id', 'in', product_ids)]}}

    @api.depends('product_id.item_total_size', 'order_id.transporter_id.trans_multi_factor')
    @api.onchange('product_id')
    def _compute_total_transport_weight(self):
        for line in self:
            if line.order_id.transporter_id:
                total_trans_weight = line.product_id.item_total_size * line.order_id.transporter_id.trans_multi_factor
                line.total_trans_weight = total_trans_weight

    @api.depends('order_id.transporter_id.tons_trans_cost', 'total_trans_weight')
    @api.onchange('product_id', 'total_trans_weight')
    def _compute_total_transport_cost(self):
        for line in self:
            total_trans_cost = 0.0
            if line.order_id.transporter_id:
                total_trans_cost = line.total_trans_weight * line.order_id.transporter_id.tons_trans_cost
            line.total_trans_cost = total_trans_cost

    @api.constrains('product_id', 'transporter_id', 'total_trans_weight')
    def _trans_total_size(self):
        """
        Prevent edit total cost to be more than the computed
        """
        for line in self:
            compute_value = line.product_id.item_total_size * line.order_id.transporter_id.trans_multi_factor
            if line.transporter_id and line.total_trans_weight > compute_value:
                raise UserError(_("%s : Total Weight ==> %s \n"
                                  "can't be more than the equation result = "
                                  "Total Size * Transporter(Trans Multi Factor) ==> %s"
                                  % (line.product_id.display_name, line.total_trans_weight, compute_value)))

    product_id = fields.Many2one(domain=_get_product_domain)
    item_type_id = fields.Many2one(related='product_id.item_type_id')
    item_type_size_eq = fields.Selection(related='item_type_id.size')
    color_id = fields.Many2one(related='product_id.color_id')
    pallet_id = fields.Many2one(related='product_id.pallet_id')
    choice_id = fields.Many2one(related='product_id.choice_id')
    length = fields.Integer(related='product_id.length')
    width = fields.Integer(related='product_id.width')
    height = fields.Integer(related='product_id.height')
    thickness = fields.Float(related='product_id.thickness')
    num_of_pieces = fields.Float(related='product_id.num_of_pieces', store=True)
    piece_size = fields.Float(related='product_id.piece_size')
    item_total_size = fields.Float(related='product_id.item_total_size')
    item_total_cost = fields.Float(related='product_id.item_total_cost')
    transporter_id = fields.Many2one(related='order_id.transporter_id')
    total_trans_weight = fields.Float("Total Weight", help="Total weight for transportation \n"
                                                           "Total Weight = Total Size * transporter(Trans Multi Factor)")
    total_trans_cost = fields.Float("Total Cost", compute=_compute_total_transport_cost, store=True,
                                    help="Total weight for transportation \n"
                                         "Total Weight = Total Size * transporter(Trans Multi Factor)")


# Ahmed Salama Code End.

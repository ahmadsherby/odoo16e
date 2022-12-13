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


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    company_seq_id = fields.Many2one('ir.sequence', "Company Seq.",
                                     help="This field is used to store company year Sequence used on account.move")

    def _create_seq_exist_companies(self, company_id):
        """
        Execute Create Sequence for company to account move by year
        :param company_id:
        :return: sequence_id
        """
        logging.info(yellow + "Generate seq for company: %s" % company_id.display_name + reset)
        seq_obj = self.env['ir.sequence']
        company_seq_id = seq_obj.create({
            'name': '%s Account Move Yearly Sequence' % company_id.display_name,
            'code': '%s.account.move.code' % company_id.display_name,
            'prefix': '%(year)s/',
            'padding': 4,
            'company_id': company_id.id
        })
        logging.info(yellow + "Seq: %s" % company_seq_id + reset)
        return company_seq_id

    @api.model
    def _generate_seq_for_exist_companies(self):
        """
        Create Sequence for company to account move by year
        """
        company_ids = self.env['res.company'].search([])
        logging.info(blue + "---- Start Generate sequences %s ----" % company_ids+ reset)
        for company in company_ids:
            if not company.company_seq_id:
                company.company_seq_id = self._create_seq_exist_companies(company)

    @api.model
    def create(self, vals):
        """
        Create Sequence for company to account move by year
        :param vals:
        :return: company_id
        """
        company_id = super().create(vals)
        company_id.company_seq_id = self._create_seq_exist_companies(company_id)
        return company_id


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    company_seq = fields.Char("Company Seq.")

    @api.model
    def create(self, vals):
        """
        Get seq from company year sequence
        :param vals:
        :return: Move
        """
        move_id = super().create(vals)
        if move_id.company_id and move_id.company_id.company_seq_id:
            move_id.company_seq = move_id.company_id.company_seq_id.next_by_id()
        return move_id


# Ahmed Salama Code End.

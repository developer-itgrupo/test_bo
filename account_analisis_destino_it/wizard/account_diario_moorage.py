# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
from datetime import *
from odoo.exceptions import UserError, ValidationError


class account_account_analytic_rep_t(models.Model):

	_name='account.account.analytic.rep.t'
	_auto = False

	periodo = fields.Char(string='Periodo',size=30)
	libro = fields.Char(string='Libro',size=30)
	voucher = fields.Char(string='Voucher',size=30)
	fecha = fields.Date('Fecha')
	partner = fields.Char(string='Partner',size=100)
	comprobante = fields.Char(string='Comprobante',size=100)
	tipo = fields.Char(string='TC',size=100)
	cuenta = fields.Char(string='Cuenta Financiera',size=100)
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	divisa = fields.Char(string='Divisa', size=30)
	importedivisa = fields.Float(string='Importe Divisa', digits=(12,2))
	ruc = fields.Char(string='RUC',size=11)
	ctaanalitica = fields.Char(string='Cta. Analítica',size=100)
	destinodebe = fields.Char(string='Destino Debe',size=100)
	destinodebename = fields.Char(string='Cuenta Destino Debe')
	destinohaber = fields.Char(string='Destino Haber',size=100)
	glosa = fields.Char(string='Glosa',size=100)
	fecha_ini = fields.Date('Fecha')
	fecha_fin = fields.Date('Fecha')


	@api.model_cr    
	def init(self):
		self.env.cr.execute("""
			drop view if exists account_account_analytic_rep_t;
			create or replace view account_account_analytic_rep_t as (

SELECT row_number() OVER () AS id,
	t.divisa,
	t.importedivisa,
	t.ruc,
	t.periodo,
	t.fecha,
	t.libro,
	t.tipo,
	t.voucher,
	t.partner,
	t.comprobante,
	t.cuenta,
	t.debe,
	t.haber,
	t.ctaanalitica,
	t.destinodebe,
	t.destinodebename,
	t.destinohaber,
	t.glosa,
	t.fecha_ini,
	t.fecha_fin
   FROM ( SELECT res_currency.name AS divisa,
			account_move_line.amount_currency AS importedivisa,
			res_partner.nro_documento AS ruc,
			account_period.name AS periodo,
			account_move.date AS fecha,
			account_journal.code AS libro,
			itd.code AS tipo,
			account_move.name AS voucher,
			res_partner.display_name AS partner,
			account_move_line.nro_comprobante AS comprobante,
			aa1.code AS cuenta,
			account_move_line.debit AS debe,
			account_move_line.credit AS haber,
			account_analytic_account.code AS ctaanalitica,
			aa3.code AS destinodebe,
			aa3.name AS destinodebename,
			aa2.code AS destinohaber,
			account_move_line.name AS glosa,
			account_period.date_start AS fecha_ini,
			account_period.date_stop AS fecha_fin
		   FROM account_move
			 JOIN account_period ON account_period.date_start <= account_move.fecha_contable and account_period.date_stop >= account_move.fecha_contable
			 JOIN account_journal ON account_move.journal_id = account_journal.id
			 JOIN account_move_line ON account_move_line.move_id = account_move.id
			 JOIN account_account aa1 ON aa1.id = account_move_line.account_id
			 JOIN account_account_type aat on aat.id = aa1.user_type_id
			 LEFT JOIN einvoice_catalog_01 itd ON itd.id = account_move_line.type_document_it
			 LEFT JOIN res_currency ON res_currency.id = account_move_line.currency_id
			 LEFT JOIN res_partner ON account_move_line.partner_id = res_partner.id
			 LEFT JOIN account_analytic_account ON account_analytic_account.id = account_move_line.analytic_account_id
			 LEFT JOIN account_account aa2 ON aa2.id =
				CASE
					WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id
					ELSE account_analytic_account.account_account_moorage_credit_id
				END
			 LEFT JOIN account_account aa3 ON aa3.id =
				CASE
					WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id
					ELSE account_analytic_account.account_account_moorage_id
				END
		  WHERE aa1.check_moorage = true and account_move.state::text = 'posted'::text AND (aa2.id is null and  aa3.id is null ) AND aat.type::text <> 'view'::text AND account_analytic_account.id IS NULL 
		UNION ALL
		 SELECT res_currency.name AS divisa,
			aml.amount_currency AS importedivisa,
			res_partner.nro_documento AS ruc,
			ap.name AS periodo,
			am.date AS fecha,
			account_journal.code AS libro,
			itd.code AS tipo,
			am.name AS voucher,
			res_partner.display_name AS partner,
			aml.nro_comprobante AS comprobante,
			aa1.code AS cuenta,
				CASE
					WHEN aal.amount < 0::numeric THEN (-1)::numeric * aal.amount
					ELSE 0::numeric
				END AS debe,
				CASE
					WHEN aal.amount > 0::numeric THEN aal.amount
					ELSE 0::numeric
				END AS haber,
			account_analytic_account.code AS ctaanalitica,
			aa3.code AS destinodebe,
			aa3.name AS destinodebename,
			aa2.code AS destinohaber,
			aml.name AS glosa,
			ap.date_start AS fecha_ini,
			ap.date_stop AS fecha_fin
		   FROM account_analytic_line aal
			 JOIN account_account aa1 ON aa1.id = aal.general_account_id
			 JOIN account_move_line aml ON aml.id = aal.move_id
			 JOIN account_move am ON am.id = aml.move_id
			 JOIN account_journal ON am.journal_id = account_journal.id
			 LEFT JOIN einvoice_catalog_01 itd ON itd.id = aml.type_document_it
			 LEFT JOIN res_currency ON res_currency.id = aml.currency_id
			 LEFT JOIN res_partner ON aml.partner_id = res_partner.id
			 LEFT JOIN account_analytic_account ON account_analytic_account.id = aal.account_id
			 LEFT JOIN account_account aa2 ON aa2.id =
				CASE
					WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id
					ELSE account_analytic_account.account_account_moorage_credit_id
				END
			 LEFT JOIN account_account aa3 ON aa3.id =
				CASE
					WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id
					ELSE account_analytic_account.account_account_moorage_id
				END
			 JOIN account_period ap ON  ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable
		  WHERE aa1.check_moorage = true and aa2.id is null and aa3.id is null
  ORDER BY 4, 6, 8) t


						)""")



class account_account_analytic_wizard_t(osv.TransientModel):
	_name='account.account.analytic.wizard.t'
	
	period_ini =fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end =fields.Many2one('account.period','Periodo Final',required=True)

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Consistencia Destinos',self.id,'account.account.analytic.wizard.t','account_analisis_destino_it.view_account_account_analytic_wizard_form_t','default_period_ini','default_period_end')

	@api.onchange('period_ini','period_end')
	def _change_periodo_ini(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return {'domain':{'period_ini':[('fiscalyear_id','=',year.id )],'period_end':[('fiscalyear_id','=',year.id )]}}

	@api.multi
	def do_rebuild(self):

		aaar_obj = self.env['account.account.analytic.rep.t']

		fechaini_obj = self.period_ini
		fechafin_obj = self.period_end
		
		lstidsaaar = aaar_obj.search([('fecha_ini','>=',fechaini_obj.date_start),('fecha_fin','<=',fechafin_obj.date_stop)])
		
		if (len(lstidsaaar) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
		
		mod_obj = self.env['ir.model.data']

		act_obj = self.env['ir.actions.act_window'] 
		print "llego"
		domain_tmp= [('fecha_ini','>=',fechaini_obj.date_start),('fecha_fin','<=',fechafin_obj.date_stop)]
		
		return {
			'domain' : domain_tmp,
			'type': 'ir.actions.act_window',
			'res_model': 'account.account.analytic.rep.t',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
		}


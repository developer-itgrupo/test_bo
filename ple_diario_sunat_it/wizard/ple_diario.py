# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
from odoo.exceptions import UserError, ValidationError
from datetime import *

class ple_diario_wizard(osv.TransientModel):
	_name='ple.diario.wizard'
	
	def get_period(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			periodos = self.env['account.period'].search([('fiscalyear_id','=',year.id)])
			periodos = filter(lambda period: not period.special and datetime.strptime(period.date_start,"%Y-%m-%d").month == datetime.now().month,periodos)
			periodos = periodos[0].id if len(periodos) > 0 else 0
			return periodos
	
	period = fields.Many2one('account.period','Periodo',default=lambda self:self.get_period())	
	tipo = fields.Selection([('diario','Diario'),('mayor','Mayor')],'Tipo', required=True)

	@api.onchange('period')
	def onchange_fiscalyear(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return {'domain':{'period':[('fiscalyear_id','=',year.id )]}}

	@api.multi
	def do_rebuild(self):

		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		if not direccion:
			raise osv.except_osv('Alerta!','No esta configurado la dirección de Directorio en Parametros')

		otro_periodo = self.period
		if self.period.code.split('/')[0]== '01':
			otro_periodo = self.env['account.period'].search([('code','=','00/' + self.period.code.split('/')[1])])[0] if self.period.code.split('/')[0]== '01' else self.period
		elif self.period.code.split('/')[0]== '12':
			otro_periodo = ( self.env['account.period'].search([('code','=','13/' + self.period.code.split('/')[1])])[0]  if len( self.env['account.period'].search([('code','=','13/' + self.period.code.split('/')[1])]) )>0 else self.period ) if self.period.code.split('/')[0]== '12' else self.period
		
		self.env.cr.execute("""		
		COPY (	
			SELECT substring(ap.code , 4, 4) || '""" + self.period.code.split('/')[0] + """' || '00' as campo1,
CASE WHEN aj.register_sunat = '1' or aj.register_sunat = '2' THEN 
substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name  || ROW_NUMBER() over( partition by substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name)
ELSE  substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name  || ROW_NUMBER() over( partition by substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name) END
as campo2,
CASE WHEN substring(ap.code,0,3)::text = '00'::text THEN 'A' || T.voucher ELSE
'M' || T.voucher END as campo3,
replace(T.cuenta, '.','') as campo4,
CASE WHEN aml.cuo_ple is null THEN '' ELSE aml.cuo_ple END as campo5,
--CASE WHEN aaa.id is not null then aaa.code else
--	case when aapi.id is not null THEN aapi.code else '' END  END as campo6,
'' as campo6,
CASE WHEN rc.id is null THEN 'PEN' else rc.name END as campo7,
CASE WHEN rp.id in (select partner_venta_boleta from main_parameter) then null::varchar else itdp.code end as campo8,
CASE WHEN rp.id in (select partner_venta_boleta from main_parameter) then null::varchar else CASE WHEN rp.nro_documento = '.' THEN 'SL' ELSE rp.nro_documento END END as campo9, 

CASE WHEN aj.register_sunat not in ('1','2') then '00' else
CASE WHEN itd.code is null THEN '00' ELSE 

CASE WHEN itd.code = 'CP' THEN '00' ELSE itd.code END END END as campo10,

CASE WHEN aj.register_sunat not in ('1','2') then NULL::text else
  CASE WHEN itd.code in ('05','50') THEN "substring"(ai.reference::text, 0, "position"(ai.reference::text, '-'::text)) ELSE
  		CASE WHEN itd.code = '10' THEN '1683' ELSE
  		CASE
  WHEN "position"(ai.reference::text, '-'::text) = 0 THEN NULL::text
  ELSE 
 
  replace(replace( repeat('0',4-char_length("substring"(ai.reference::text, 0, "position"(ai.reference::text, '-'::text)))) || "substring"(ai.reference::text, 0, "position"(ai.reference::text, '-'::text)),'/','-'),'|','-') END
END END END as campo11,


CASE WHEN aj.register_sunat not in ('1','2') then am.name else

CASE WHEN itd.code is null THEN am.name else 
CASE
  WHEN "position"(ai.reference::text, '-'::text) = 0 THEN ai.reference::text
  ELSE "substring"(ai.reference::text, "position"(ai.reference::text, '-'::text) + 1)
END END END as campo12,
''::varchar as campo13,
''::varchar as campo14,
--CASE WHEN am.date is null THEN '' ELSE (to_char( am.date::date , 'DD/MM/YYYY'))::varchar END as campo13,
--CASE WHEN aml.date_maturity is null THEN '' ELSE (to_char( aml.date_maturity::date , 'DD/MM/YYYY'))::varchar END as campo14,
CASE WHEN am.date is null THEN '' ELSE (to_char( am.date::date , 'DD/MM/YYYY'))::varchar END  as campo15,
replace(replace(aml.name,'/','-'),'|','-') as campo16,
'' as campo17,
round(aml.debit,2) as campo18,
round(aml.credit,2) as campo19,

CASE WHEN false = true THEN '' else 

CASE WHEN aj.register_sunat = '2' THEN '140100' || '&' ||  ( substring(ap.code , 4, 4) || substring(ap.code, 0,3) || '00' )  || '&' || T.aml_id || '&' || ('M' || T.voucher) ELSE
	CASE WHEN (aj.register_sunat = '1') and rp.is_resident = true THEN  '080200'  || '&' ||  ( substring(ap.code , 4, 4) || substring(ap.code, 0,3) || '00' )  || '&' || T.aml_id || '&' || ('M' || T.voucher) ELSE
		CASE WHEN (aj.type = 'purchase' or aj.type = 'purchase_refund') and (rp.is_resident = false or rp.is_resident is null) THEN '080100'  || '&' ||  ( substring(ap.code , 4, 4) || substring(ap.code, 0,3) || '00' )  || '&' || T.aml_id || '&' || ('M' || T.voucher) ELSE '' END
	END
END END as campo20,
am.ple_diariomayor as campo21,
'' as campo22

from get_libro_diario(0,219001) AS T
inner join account_period ap on ap.id = T.ap_id
inner join account_move am on am.id = T.am_id
left join account_invoice ai on ai.move_id = am.id
inner join account_move_line aml on aml.id = T.aml_id
left join einvoice_catalog_01 itd on itd.id = ai.it_type_document
inner join account_journal aj on aj.id = am.journal_id
left join account_period ap2 on ap2.date_start <= am.fecha_modify_ple and ap2.date_stop >= am.fecha_modify_ple and am.fecha_special = ap2.special
left join account_analytic_account aaa on aaa.id = aml.analytic_account_id
left join res_currency rc on aml.currency_id = rc.id
left join res_partner rp on rp.id = aml.partner_id
left join einvoice_catalog_06 itdp on itdp.id = rp.type_document_partner_it
left join res_partner rp_nd on rp_nd.id = ai.beneficiario_de_pagos
where ( ap.id = """ + str(self.period.id) +""" or ap.id = """ + str(otro_periodo.id) +""" )  
)
TO '""" + str( direccion + 'plediario.csv') + """'
with delimiter '|'
""")

		ruc = self.env['res.company'].search([])[0].partner_id.nro_documento
		mond = self.env['res.company'].search([])[0].currency_id.name

		if not ruc:
			raise osv.except_osv('Alerta!', 'No esta configurado el RUC en la compañia')

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		file_name = 'a.txt'
		
		txt_act = None
		corredor = 1
		exp_r = []
		exp_r = open( str( direccion + 'plediario.csv' ), 'r').readlines()

		exp = ("".join(exp_r) ).replace('\\N','').replace('|0.0|','|0.00|')
		
		nombre_respec = ''
		if self.tipo == 'diario':
			nombre_respec = 'LE' + ruc + self.period.code[3:7]+ self.period.code[:2]+'00050100001' +('1' if len(exp)  >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt'
		else:
			nombre_respec = 'LE' + ruc + self.period.code[3:7]+ self.period.code[:2]+'00060100001' +('1' if len(exp)  >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt'

		vals = {
			'output_name': nombre_respec,
			'output_file': base64.encodestring(  "-- Sin Registros --" if exp =="" else exp ),
			'respetar':1,	
		}

		sfs_id = self.env['export.file.save'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}




class ple_diario_contable_wizard(osv.TransientModel):
	_name='ple.diario.contable.wizard'
	
	def get_period(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			periodos = self.env['account.period'].search([('fiscalyear_id','=',year.id)])
			periodos = filter(lambda period: not period.special and datetime.strptime(period.date_start,"%Y-%m-%d").month == datetime.now().month,periodos)
			periodos = periodos[0].id if len(periodos) > 0 else 0
			return periodos

	period = fields.Many2one('account.period','Periodo',default=lambda self:self.get_period())
	
	@api.onchange('period')
	def onchange_fiscalyear(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return {'domain':{'period':[('fiscalyear_id','=',year.id )]}}

	@api.multi
	def do_rebuild(self):
		"""
		self.env.cr.execute(""
			SELECT T.*,
am.ple_diariomayor
from get_libro_diario(false,0,219001) AS T
inner join account_period ap on ap.id = T.ap_id
inner join account_move am on am.id = T.am_id
inner join account_period ap2 on ap2.id = am.period_modify_ple
where ap2.id = ""+ str(self.period.id) + "" "")
		tra = self.env.cr.fetchall()
		"""
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		m_code_sunat = None
		if self.env['main.parameter'].search([])[0].template_account_contable:
			m_code_sunat = self.env['main.parameter'].search([])[0].template_account_contable.code_sunat
		else:
			raise exceptions.Warning(_("No esta configurado la Plantilla para el Codigo Sunat")) 
		rpta = ""

		verf_unique = {}

		for i in self.env['account.account'].search([('user_type_id.type','!=','view'),('level_sheet','=',2)]):
			rpta += (unicode(self.period.code[3:7]+ self.period.code[:2]+ self.period.date_stop[8:10] )).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( str(i.code).replace('.','') )).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( str(i.name)[:99].replace('/','-'))).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( str(m_code_sunat) )).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( '-' if str(m_code_sunat)!= '99' else '' )).encode('iso-8859-1','ignore')+ '|'+ '|'+ '|'
			rpta += (unicode( '1' )).encode('iso-8859-1','ignore')+ '|' + '\n'
		ruc = self.env['res.company'].search([])[0].partner_id.nro_documento
		mond = self.env['res.company'].search([])[0].currency_id.name


		if not ruc:
			raise osv.except_osv('Alerta!', 'No esta configurado el RUC en la compañia')
		
		vals = {
			'output_name': 'LE' + ruc + self.period.code[3:7]+ self.period.code[:2]+'0005030000'+ '1'+('1') + ('1' if mond == 'PEN' else '2') +'1.txt',
			'output_file': base64.encodestring("-- Sin Registros --" if rpta == "" else rpta ),	
			'respetar':1,	
		}



		sfs_id = self.env['export.file.save'].create(vals)
		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}

# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
import os
from odoo.exceptions import UserError, ValidationError
from datetime import *

class ple_sale_wizard(osv.TransientModel):
	_name='ple.sale.wizard'
	
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
	tipo_ple = fields.Selection([('141','14.1'),('142','14.2')], string="Formato",required=True)

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
		period = self.period
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		
		if self.tipo_ple == '141':
			self.env.cr.execute("""
			COPY (select 
CASE WHEN ap.code is not Null THEN substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || '00' ELSE '' END as campo1,
substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name as campo2,
--CASE WHEN compra.am_id is not Null THEN (compra.am_id)::varchar ELSE '' END as campo2,
CASE WHEN compra.voucher is not Null THEN  'M' || reverse( substring ( reverse(compra.voucher) , 0 , (CASE WHEN position('/' in reverse(compra.voucher))= 0 THEN 1000 ELSE position('/' in reverse(compra.voucher)) END)  ) ) ELSE '' END as campo3,
CASE WHEN compra.fechaemision is not Null THEN (to_char( compra.fechaemision::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo4,
CASE WHEN compra.fechavencimiento is not Null and compra.tipodocumento = '14' THEN (to_char( compra.fechavencimiento::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo5,
CASE WHEN anulado.name = compra.partner and anulado.nro_documento = compra.numdoc THEN '00' ELSE
	CASE WHEN compra.tipodocumento is not Null THEN 
		CASE WHEN compra.tipodocumento = 'CP' THEN '00' ELSE compra.tipodocumento END
		ELSE '' 
	END END as campo6,
CASE WHEN compra.serie is not Null THEN repeat('0',4-char_length(compra.serie)) || replace(compra.serie,'/','-') ELSE '' END as campo7,
CASE WHEN compra.numero is not Null THEN compra.numero ELSE '' END as campo8,
CASE WHEN ai.numero_final_consolidado_cliente is not Null THEN ai.numero_final_consolidado_cliente::varchar else '' END as campo9,

CASE WHEN (anulado.name = compra.partner and anulado.nro_documento = compra.numdoc) or (ventaboleta.name = compra.partner and ventaboleta.nro_documento = compra.numdoc) THEN '' ELSE
CASE WHEN compra.tipodoc is not Null THEN compra.tipodoc::varchar ELSE '' END end as campo10,

CASE WHEN (anulado.name = compra.partner and anulado.nro_documento = compra.numdoc) or (ventaboleta.name = compra.partner and ventaboleta.nro_documento = compra.numdoc) THEN '' ELSE
CASE WHEN compra.numdoc is not Null THEN compra.numdoc ELSE '' END END as campo11,

CASE WHEN (anulado.name = compra.partner and anulado.nro_documento = compra.numdoc) or (ventaboleta.name = compra.partner and ventaboleta.nro_documento = compra.numdoc) THEN '' ELSE
CASE WHEN compra.partner is not Null THEN compra.partner ELSE '' END END as campo12,

CASE WHEN compra.valorexp is not Null THEN (compra.valorexp)::varchar ELSE '0.00' END as campo13,
CASE WHEN compra.baseimp is not Null THEN (compra.baseimp)::varchar ELSE '0.00' END as campo14,
'0.00'::varchar as campo15,
CASE WHEN compra.igv is not Null THEN (compra.igv)::varchar  ELSE '0.00' END as campo16,
'0.00'::varchar as campo17,
CASE WHEN compra.exonerado is not Null THEN (compra.exonerado )::varchar ELSE '0.00' END as campo18,
CASE WHEN compra.inafecto is not Null THEN (compra.inafecto)::varchar ELSE '0.00' END as campo19,
CASE WHEN compra.isc is not Null THEN (compra.isc)::varchar ELSE '0.00' END as campo20,
'0.00'::varchar as campo21,
'0.00'::varchar as campo22,
CASE WHEN compra.otros is not Null THEN (compra.otros)::varchar ELSE '0.00' END as campo23,
CASE WHEN compra.total is not Null THEN (compra.total)::varchar ELSE '0.00' END as campo24,
CASE WHEN compra.divisa is not Null THEN 
	CASE WHEN compra.divisa = 'PEN' THEN '' ELSE compra.divisa END
ELSE '' END as campo25,
CASE WHEN compra.tipodecambio is not Null THEN ( round(compra.tipodecambio,3) )::varchar ELSE '' END as campo26,
CASE WHEN compra.fechadm is not Null THEN (to_char( compra.fechadm::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo27,
CASE WHEN compra.tipodocmod is not Null THEN compra.tipodocmod ELSE '' END as campo28,
CASE WHEN compra.seriemod is not Null THEN repeat('0',4-char_length(compra.seriemod)) || compra.seriemod ELSE '' END as campo29,
CASE WHEN compra.numeromod is not Null THEN compra.numeromod ELSE '' END as campo30,
CASE WHEN ai.numero_contrato_cliente is not Null THEN ai.numero_contrato_cliente else '' end as campo31,
CASE WHEN ai.inconsistencia_tipo_cambio_cliente THEN '1' else '' END as campo32,
CASE WHEN ai.cancelado_medio_pago_cliente THEN '1' ELSE '' END as campo33,
ai.estado_ple_venta as campo34,
'' as campo35
from get_venta_1_1_1(0,209501) compra
inner join account_period ap on ap.name = compra.periodo
inner join account_move am on am.id = compra.am_id
	inner join account_invoice ai on ai.move_id = am.id
	left join account_period ap2 on ap2.date_start <= am.fecha_modify_ple_venta and ap2.date_stop >= am.fecha_modify_ple_venta and ap2.special = am.fecha_special
cross join main_parameter 
left join res_partner anulado on anulado.id = main_parameter.partner_null_id
left join res_partner ventaboleta on ventaboleta.id = main_parameter.partner_venta_boleta
inner join account_journal aj on aj.id = am.journal_id
where ap2.id = """+ str(self.period.id) + """ or ap.id = """+ str(self.period.id) + """) 
TO '"""+ str( direccion + 'sale.csv' )+ """'
with delimiter '|'
		""")

		if self.tipo_ple == '142':
			
			self.env.cr.execute("""
			COPY (select 
CASE WHEN ap.code is not Null THEN substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || '00' ELSE '' END as campo1,
substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name as campo2,
--CASE WHEN compra.am_id is not Null THEN (compra.am_id)::varchar ELSE '' END as campo2,
CASE WHEN compra.voucher is not Null THEN  'M' || reverse( substring ( reverse(compra.voucher) , 0 , (CASE WHEN position('/' in reverse(compra.voucher))= 0 THEN 1000 ELSE position('/' in reverse(compra.voucher)) END)  ) ) ELSE '' END as campo3,
CASE WHEN compra.fechaemision is not Null THEN (to_char( compra.fechaemision::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo4,
CASE WHEN compra.fechavencimiento is not Null and compra.tipodocumento = '14' THEN (to_char( compra.fechavencimiento::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo5,
CASE WHEN anulado.name = compra.partner and anulado.nro_documento = compra.numdoc THEN '00' ELSE
	CASE WHEN compra.tipodocumento is not Null THEN 
		CASE WHEN compra.tipodocumento = 'CP' THEN '00' ELSE compra.tipodocumento END
		ELSE '' 
	END END as campo6,
CASE WHEN compra.serie is not Null THEN repeat('0',4-char_length(compra.serie)) || compra.serie ELSE '' END as campo7,
CASE WHEN compra.numero is not Null THEN compra.numero ELSE '' END as campo8,
CASE WHEN ai.numero_final_consolidado_cliente is not Null THEN ai.numero_final_consolidado_cliente::varchar else '' END as campo9,
CASE WHEN compra.tipodoc is not Null THEN compra.tipodoc::integer ELSE 0 END as campo10,
CASE WHEN compra.numdoc is not Null THEN compra.numdoc ELSE '' END as campo11,
CASE WHEN compra.partner is not Null THEN compra.partner ELSE '' END as campo12,
CASE WHEN compra.baseimp is not Null THEN (compra.baseimp)::varchar ELSE '0.00' END as campo13,
CASE WHEN compra.igv is not Null THEN (compra.igv)::varchar  ELSE '0.00' END as campo14,
CASE WHEN compra.otros is not Null THEN (compra.otros)::varchar ELSE '0.00' END as campo15,
CASE WHEN compra.total is not Null THEN (compra.total)::varchar ELSE '0.00' END as campo16,
CASE WHEN compra.divisa is not Null THEN 
	CASE WHEN compra.divisa = 'PEN' THEN '' ELSE compra.divisa END
ELSE '' END as campo17,
CASE WHEN compra.tipodecambio is not Null THEN ( round(compra.tipodecambio,3) )::varchar ELSE '' END as campo18,
CASE WHEN compra.fechadm is not Null THEN (to_char( compra.fechadm::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo19,
CASE WHEN compra.tipodocmod is not Null THEN compra.tipodocmod ELSE '' END as campo20,
CASE WHEN compra.seriemod is not Null THEN repeat('0',4-char_length(compra.seriemod)) || compra.seriemod ELSE '' END as campo21,
CASE WHEN compra.numeromod is not Null THEN compra.numeromod ELSE '' END as campo22,
CASE WHEN ai.inconsistencia_tipo_cambio_cliente THEN '1' else '' END as campo23,
CASE WHEN ai.cancelado_medio_pago_cliente THEN '1' ELSE '' END as campo24,
ai.estado_ple_venta as campo25,
'' as campo26
from get_venta_1_1_1(0,209501) compra
inner join account_period ap on ap.name = compra.periodo
inner join account_move am on am.id = compra.am_id
	inner join account_invoice ai on ai.move_id = am.id
	left join account_period ap2 on ap2.date_start <= am.fecha_modify_ple_venta and ap2.date_stop >= am.fecha_modify_ple_venta and ap2.special = am.fecha_special
inner join account_journal aj on aj.id = am.journal_id
cross join main_parameter 
left join res_partner anulado on anulado.id = main_parameter.partner_null_id
left join res_partner ventaboleta on ventaboleta.id = main_parameter.partner_venta_boleta
where ap2.id = """+ str(self.period.id) + """  or ap.id = """+ str(self.period.id) + """)
TO '"""+ str( direccion + 'sale.csv' )+ """'
with delimiter '|'
		""")


		ruc = self.env['res.company'].search([])[0].partner_id.nro_documento
		mond = self.env['res.company'].search([])[0].currency_id.name

		if not ruc:
			raise osv.except_osv('Alerta!', 'No esta configurado el RUC en la compañia')

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		file_name = 'a.txt'
			
		exp = "".join(open( str( direccion + 'sale.csv' ), 'r').readlines() ) 
		

		direccion_ple = self.env['main.parameter'].search([])[0].dir_ple_create_file


		if not direccion_ple:
			raise osv.except_osv('Alerta!', 'No esta configurado el directorio para los PLE Sunat en parametros.')
			

		name_camb = ""	
		if self.tipo_ple == "141":
			name_camb = "00140100001"
		if self.tipo_ple == "142":
			name_camb = "00140200001"




		vals = {
			'output_name': 'LE' + ruc + self.period.code[3:7]+ self.period.code[:2]+name_camb+('1' if len(exp) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt',
			'output_file': base64.encodestring(  "== Sin Registros ==" if exp =="" else exp ),		
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


# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import os
from odoo.exceptions import UserError, ValidationError
from datetime import *

class ple_purchase_register_wizard(osv.TransientModel):
	_name = 'ple.purchase.register.wizard'

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

	period_ini = fields.Many2one('account.period', 'Periodo', required=True,default=lambda self:self.get_period())
	tipo_ple = fields.Selection(
		[('81', '8.1'), ('82', '8.2'), ('83', '8.3')], string="Formato", required=True)

	@api.onchange('period_ini')
	def onchange_fiscalyear(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return {'domain':{'period_ini':[('fiscalyear_id','=',year.id )]}}

	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		dat = self.period_ini.name.split('/')
		anho = dat[1]
		mes = dat[0]
		period_ini = anho+mes+'00'
		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		if not direccion:
			raise osv.except_osv(
				'Alerta!', 'No esta configurado la dirección de Directorio en Parametros')

		if self.tipo_ple == '81':
			query="""
			COPY (select * from (select  distinct
			CASE WHEN ap.code is not Null THEN substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || '00' ELSE '' END as campo1,

			substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name as campo2,
			--CASE WHEN ai_ple.id is not Null THEN ai_ple.id || 'AI' ELSE compra.am_id || 'AM' END as campo2,
			-- CASE WHEN compra.am_id is not Null THEN (compra.am_id)::varchar ELSE '' END as campo2,
			CASE WHEN compra.voucher is not Null THEN  'M' || reverse( substring ( reverse(compra.voucher) , 0 , (CASE WHEN position('/' in reverse(compra.voucher))= 0 THEN 1000 ELSE position('/' in reverse(compra.voucher)) END)  ) ) ELSE '' END as campo3,
			CASE WHEN compra.fechaemision is not Null THEN (to_char( compra.fechaemision::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo4,
			CASE WHEN compra.fechavencimiento is not Null and compra.tipodocumento = '14' THEN (to_char( compra.fechavencimiento::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo5,
			CASE WHEN anulado.name = compra.razonsocial and anulado.nro_documento = compra.ruc THEN '00' ELSE
				CASE WHEN compra.tipodocumento is not Null THEN 
					CASE WHEN compra.tipodocumento = 'CP' THEN '00' ELSE compra.tipodocumento END
				ELSE '' 
			END END as campo6,
			CASE WHEN compra.tipodocumento = '05' or compra.tipodocumento = '50' THEN compra.serie else
			CASE WHEN compra.tipodocumento = '10' THEN '1683' ELSE
			CASE WHEN compra.serie is not Null THEN repeat('0',4-char_length(compra.serie)) || compra.serie ELSE '' END END END as campo7,
			CASE WHEN compra.tipodocumento in ('50','52') THEN substring(ap.code,4,5 ) else '' END as campo8,
			CASE WHEN compra.numero is not Null THEN compra.numero ELSE '' END as campo9,
			CASE WHEN ai.ultimo_numero_consolidado is not Null THEN ai.ultimo_numero_consolidado::varchar ELSE ''::varchar END as campo10,

				CASE WHEN anulado.name = compra.razonsocial and anulado.nro_documento = compra.ruc THEN '' ELSE
			CASE WHEN compra.tdp is not Null THEN compra.tdp ELSE '' END END as campo11,

			CASE WHEN anulado.name = compra.razonsocial and anulado.nro_documento = compra.ruc THEN '' ELSE
			CASE WHEN compra.ruc is not Null THEN compra.ruc ELSE '' END END as campo12,

			CASE WHEN anulado.name = compra.razonsocial and anulado.nro_documento = compra.ruc THEN '' ELSE
			CASE WHEN compra.razonsocial is not Null THEN compra.razonsocial ELSE '' END END as campo13,
			CASE WHEN compra.bioge is not Null THEN (compra.bioge)::varchar ELSE '0.00' END as campo14,
			CASE WHEN compra.igva is not Null THEN (compra.igva)::varchar ELSE '0.00' END as campo15,
			CASE WHEN compra.biogeng is not Null THEN (compra.biogeng)::varchar ELSE '0.00' END as campo16,
			CASE WHEN compra.igvb is not Null THEN (compra.igvb)::varchar ELSE '0.00' END as campo17,
			CASE WHEN compra.biong is not Null THEN (compra.biong)::varchar ELSE '0.00' END as campo18,
			CASE WHEN compra.igvc is not Null THEN (compra.igvc)::varchar  ELSE '0.00' END as campo19,
			CASE WHEN compra.cng is not Null THEN (compra.cng)::varchar ELSE '0.00' END as campo20,
			CASE WHEN compra.isc is not Null THEN (compra.isc)::varchar ELSE '0.00' END as campo21,
			CASE WHEN compra.otros is not Null THEN (compra.otros)::varchar ELSE '0.00' END as campo22,
			CASE WHEN compra.total is not Null THEN (compra.total)::varchar ELSE '0.00' END as campo23,
			CASE WHEN compra.moneda is not Null THEN 
			CASE WHEN compra.moneda = 'PEN' THEN '' ELSE compra.moneda END
			ELSE '' END as campo24,
			CASE WHEN compra.tc is not Null THEN ( round(compra.tc,3) )::varchar ELSE '' END as campo25,
			CASE WHEN compra.fechadm is not Null THEN (to_char( compra.fechadm::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo26,
			CASE WHEN compra.td is not Null THEN compra.td ELSE '' END as campo27,
			CASE WHEN compra.seried is not Null THEN repeat('0',4-char_length(compra.seried)) || compra.seried ELSE '' END as campo28,
			CASE WHEN compra.td in ('50','52') THEN compra.seried ELSE '' END as campo29,
			CASE WHEN compra.numerodd is not Null THEN compra.numerodd ELSE '' END as campo30,

			CASE WHEN compra.fechad is not Null THEN (to_char( compra.fechad::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo31,
			CASE WHEN compra.numerod is not Null THEN compra.numerod ELSE '' END as campo32,

			CASE WHEN ai.sujeto_a_retencion THEN '1'::varchar ELSE ''::varchar END as campo33,
			CASE WHEN ai.tipo_adquisicion is not Null THEN ai.tipo_adquisicion::varchar ELSE ''::varchar END as campo34,
			CASE WHEN ai.contrato_o_proyecto is not Null THEN ai.contrato_o_proyecto::varchar else ''::varchar END as campo35,
			CASE WHEN ai.inconsistencia_tipo_cambio THEN '1'::varchar ELSE ''::varchar END as campo36,
			CASE WHEN ai.proveedor_no_habido THEN '1'::varchar ELSE ''::varchar END as campo37,
			CASE WHEN ai.renuncio_a_exoneracion_igv THEN '1'::varchar ELSE ''::varchar END as campo38,
			CASE WHEN ai.inconsistencia_dni_liquidacion_comp THEN '1'::varchar ELSE ''::varchar END as campo39,
			CASE WHEN ai.cancelado_medio_pago THEN '1'::varchar ELSE ''::varchar END as campo40,

			ai.estado_ple_compra as campo41,
			'' as campo35
			from get_compra_1_1_1(0,219001) compra
			inner join account_period ap on ap.name = compra.periodo
			inner join account_move am on am.id = compra.am_id
			inner join account_invoice ai on ai.move_id = am.id
			left join res_partner rp_veri on rp_veri.id = am.partner_id
			inner join account_journal aj on aj.id = am.journal_id
			cross join main_parameter
			left join res_partner anulado on anulado.id = main_parameter.partner_null_id
			where coalesce(rp_veri.is_resident,false) = false
			) as T
			where ( campo1 ='"""+period_ini+"""'  )  )  
			TO '""" + str(direccion + 'purchase.csv') + """'
			with delimiter '|'
			"""
			self.env.cr.execute(query)

		if self.tipo_ple == '82':
			self.env.cr.execute("""
COPY ( select * from (select  distinct
CASE WHEN ap.code is not Null THEN substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || '00' ELSE '' END as campo1,
substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name as campo2,
CASE WHEN compra.voucher is not Null THEN  'M' || reverse( substring ( reverse(compra.voucher) , 0 , (CASE WHEN position('/' in reverse(compra.voucher))= 0 THEN 1000 ELSE position('/' in reverse(compra.voucher)) END)  ) ) ELSE '' END as campo3,
CASE WHEN compra.fechaemision is not Null THEN (to_char( compra.fechaemision::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo4,
CASE WHEN anulado.name = compra.razonsocial and anulado.nro_documento = compra.ruc THEN '00' ELSE
compra.tipodocumento END as campo5,
CASE
WHEN "position"(ai.reference::text, '-'::text) = 0 THEN ''
ELSE "substring"(ai.reference::text, 0, "position"(ai.reference::text, '-'::text))
END 
aS campo6,
CASE
WHEN "position"(ai.reference::text, '-'::text) = 0 THEN ai.reference::text
ELSE "substring"(ai.reference::text, "position"(ai.reference::text, '-'::text) + 1)
END AS CAMPO7,
CASE WHEN compra.bioge is not Null THEN (compra.bioge)::varchar ELSE '0.00' END as campo8,
CASE WHEN compra.otros is not Null THEN (compra.otros)::varchar ELSE '0.00' END as campo9,
CASE WHEN compra.total is not Null THEN (compra.total)::varchar ELSE '0.00' END as campo10,
CASE WHEN ai.tipo_sustento_credito_fiscasl is not Null THEN ai.tipo_sustento_credito_fiscasl ELSE '' END as campo11,
CASE WHEN ai.serie_sustento_credito_fiscasl is not Null THEN ai.serie_sustento_credito_fiscasl ELSE '' END as campo12,
CASE WHEN ai.anio_sustento_credito_fiscasl is not Null THEN ai.anio_sustento_credito_fiscasl ELSE '' END as campo13,
CASE WHEN ai.nro_comp_sustento_credito_fiscasl is not Null THEN ai.nro_comp_sustento_credito_fiscasl ELSE '' END as  campo14,
CASE WHEN ai.impuesto_retenido is not Null THEN ai.impuesto_retenido ELSE 0.00 END as campo15,
compra.moneda as campo16,
CASE WHEN compra.tc is not Null THEN (  round(compra.tc,3) )::varchar ELSE '' END as campo17,
CASE WHEN rp.pais_residencia_nd is not Null THEN rp.pais_residencia_nd::varchar ELSE '' END as campo18,
CASE WHEN rp.name is not Null THEN rp.name::varchar ELSE '' END as campo19,
CASE WHEN rp.domicilio_extranjero_nd is not Null THEN rp.domicilio_extranjero_nd::varchar ELSE '' END as campo20,
rp.nro_documento as campo21,
CASE WHEN rpb.numero_identificacion_nd is not Null THEN rpb.numero_identificacion_nd::varchar ELSE '' END as campo22,
CASE WHEN rpb.name is not Null THEN rpb.name::varchar ELSE '' END as campo23,
CASE WHEN rpb.pais_residencia_nd is not Null THEN rpb.pais_residencia_nd::varchar ELSE '' END as campo24,
CASE WHEN rp.vinculo_contribuyente_residente_extranjero is not Null THEN rp.vinculo_contribuyente_residente_extranjero::varchar ELSE '' END as campo25,
CASE WHEN ai.renta_bruta is not Null THEN ai.renta_bruta::varchar ELSE '' END as campo26,
CASE WHEN ai.deduccion_costo_enajenacion is not Null THEN ai.deduccion_costo_enajenacion::varchar ELSE '' END as campo27,
CASE WHEN ai.renta_neta is not Null THEN ai.renta_neta::varchar ELSE '' END as campo28,
CASE WHEN ai.tasa_de_retencion is not Null THEN ai.tasa_de_retencion::varchar ELSE '' END as campo29,
CASE WHEN ai.impuesto_retenido is not Null THEN ai.impuesto_retenido ELSE 0.00 END as campo30,
CASE WHEN rp.convenios_evitar_doble_imposicion is not Null THEN rp.convenios_evitar_doble_imposicion::varchar ELSE '' END as campo31,
CASE WHEN ai.exoneracion_aplicada is not Null THEN ai.exoneracion_aplicada::varchar ELSE '' END as campo32,
CASE WHEN ai.tipo_de_renta is not Null THEN ai.tipo_de_renta::varchar ELSE '' END as campo33,
CASE WHEN ai.modalidad_servicio_prestada is not Null THEN  ai.modalidad_servicio_prestada::varchar ELSE ''  END as campo34,
CASE WHEN ai.aplica_art_del_impuesto THEN '1'::varchar ELSE ''::varchar END as campo35,
ai.estado_ple_compra as campo36,
'' as campo37
from get_compra_1_1_1(0,219001) compra
inner join account_period ap on ap.name = compra.periodo
inner join account_move am on am.id = compra.am_id
inner join account_invoice ai on ai.move_id = am.id
left join account_period ap2 on ap2.date_start <= am.fecha_modify_ple_compra and ap2.date_stop >= am.fecha_modify_ple_compra and ap2.special = am.fecha_special
left join res_partner rp on rp.id = am.partner_id
left join res_partner rpb on rpb.id = ai.beneficiario_de_pagos
inner join account_journal aj on aj.id = am.journal_id
cross join main_parameter 
left join res_partner anulado on anulado.id = main_parameter.partner_null_id
where  (rp.is_resident=TRUE) and  ( ap2.id = """+ str(self.period_ini.id) + """ or ap.id = """+ str(self.period_ini.id) + """ )) as TOTALCS where campo5 in ('00','91','97','98') )  
TO '"""+ str( direccion +  'purchase.csv' )+ """'
with delimiter '|'
			""")


		if self.tipo_ple == '83':
			query = """
			COPY ( select * from (select  distinct
			CASE WHEN ap.code is not Null THEN substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || '00' ELSE '' END as campo1,
			substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name as campo2,
			--CASE WHEN ai_ple.id is not Null THEN ai_ple.id || 'AI' ELSE compra.am_id || 'AM' END as campo2,
			-- CASE WHEN compra.am_id is not Null THEN (compra.am_id)::varchar ELSE '' END as campo2,
			CASE WHEN compra.voucher is not Null THEN  'M' || reverse( substring ( reverse(compra.voucher) , 0 , (CASE WHEN position('/' in reverse(compra.voucher))= 0 THEN 1000 ELSE position('/' in reverse(compra.voucher)) END)  ) ) ELSE '' END as campo3,
			CASE WHEN compra.fechaemision is not Null THEN (to_char( compra.fechaemision::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo4,
			CASE WHEN compra.fechavencimiento is not Null THEN (to_char( compra.fechavencimiento::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo5,
			CASE WHEN anulado.name = compra.razonsocial and anulado.nro_documento = compra.ruc THEN '00' ELSE
				CASE WHEN compra.tipodocumento is not Null THEN 
					CASE WHEN compra.tipodocumento = 'CP' THEN '00' ELSE compra.tipodocumento END
				ELSE '' 
			END END as campo6,
			CASE WHEN compra.tipodocumento = '10' THEN '1683' ELSE
			CASE WHEN compra.serie is not Null THEN repeat('0',4-char_length(compra.serie)) || compra.serie ELSE '' END END as campo7,
			CASE WHEN compra.numero is not Null THEN compra.numero ELSE '' END as campo8,
			CASE WHEN ai.ultimo_numero_consolidado is not Null THEN ai.ultimo_numero_consolidado::varchar ELSE ''::varchar END as campo9,
			CASE WHEN compra.tdp is not Null THEN ((compra.tdp)::integer)::varchar ELSE '' END as campo10,
			CASE WHEN compra.ruc is not Null THEN compra.ruc ELSE '' END as campo11,
			CASE WHEN anulado.name = compra.razonsocial and anulado.nro_documento = compra.ruc THEN '' ELSE
			CASE WHEN compra.razonsocial is not Null THEN compra.razonsocial ELSE '' END END as campo12,


			CASE WHEN compra.bioge is not Null THEN (compra.bioge)::varchar ELSE '0.00' END as campo13,
			CASE WHEN compra.igva is not Null THEN (compra.igva)::varchar ELSE '0.00' END as campo14,
			CASE WHEN compra.otros is not Null THEN (compra.otros)::varchar ELSE '0.00' END as campo15,
			CASE WHEN compra.total is not Null THEN (compra.total)::varchar ELSE '0.00' END as campo16,


			CASE WHEN compra.moneda is not Null THEN 
			CASE WHEN compra.moneda = 'PEN' THEN '' ELSE compra.moneda END
			ELSE '' END as campo17,


			CASE WHEN compra.tc is not Null THEN ( round(compra.tc,3))::varchar ELSE '' END as campo18,
			CASE WHEN compra.fechadm is not Null THEN (to_char( compra.fechadm::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo19,
			CASE WHEN compra.td is not Null THEN compra.td ELSE '' END as campo20,
			CASE WHEN compra.seried is not Null THEN repeat('0',4-char_length(compra.seried)) || compra.seried ELSE '' END as campo21,
			CASE WHEN compra.numerodd is not Null THEN compra.numerodd ELSE '' END as campo22,

			CASE WHEN compra.fechad is not Null THEN (to_char( compra.fechad::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo23,
			CASE WHEN compra.numerod is not Null THEN compra.numerod ELSE '' END as campo24,

			CASE WHEN ai.sujeto_a_retencion THEN '1'::varchar ELSE ''::varchar END  as campo25,


			CASE WHEN ai.tipo_adquisicion is not Null THEN ai.tipo_adquisicion::varchar ELSE ''::varchar END as campo26,


			CASE WHEN ai.inconsistencia_tipo_cambio THEN '1'::varchar ELSE ''::varchar END as campo27,
			CASE WHEN ai.proveedor_no_habido THEN '1'::varchar ELSE ''::varchar END as campo28,
			CASE WHEN ai.renuncio_a_exoneracion_igv THEN '1'::varchar ELSE ''::varchar END as campo29,
			CASE WHEN ai.cancelado_medio_pago THEN '1'::varchar ELSE ''::varchar END as campo30,

			ai.estado_ple_compra as campo31,
			'' as campo32
			from get_compra_1_1_1(0,219001) compra
			inner join account_period ap on ap.name = compra.periodo
			inner join account_move am on am.id = compra.am_id
			inner join account_invoice ai on ai.move_id = am.id
			inner join account_journal aj on aj.id = am.journal_id
			cross join main_parameter 
			left join res_partner anulado on anulado.id = main_parameter.partner_null_id
					) as T where ( campo1 ='"""+period_ini+"""' )    )
			TO '""" + str(direccion + 'purchase.csv') + """'
			with delimiter '|'
			"""
			self.env.cr.execute(query)
		# CASE WHEN ap.id != ap2.id THEN (CASE WHEN am.ckeck_modify_ple THEN  '9' ELSE '8' END ) ELSE '1' END as campo34,

		ruc = self.env['res.company'].search([])[0].partner_id.nro_documento
		mond = self.env['res.company'].search([])[0].currency_id.name

		if not ruc:
			raise osv.except_osv(
				'Alerta!', 'No esta configurado el RUC en la compañia')

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		file_name = 'a.txt'

		exp = "".join(open(str(direccion + 'purchase.csv'), 'r').readlines())

		# vals = {
		#	'output_name': 'LE' + ruc + self.period_ini.code[3:7]+ self.period_ini.code[:2]+'00080100001'+('1' if len(exp) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt',
		#	'output_file': base64.encodestring(  "\r\n" if exp =="" else exp ),
		# }

		direccion_ple = self.env['main.parameter'].search([])[
			0].dir_ple_create_file

		if not direccion_ple:
			raise osv.except_osv(
				'Alerta!', 'No esta configurado el directorio para los PLE Sunat en parametros.')

		name_camb = ""
		if self.tipo_ple == "81":
			name_camb = "00080100001"
		if self.tipo_ple == "82":
			name_camb = "00080200001"
		if self.tipo_ple == "83":
			name_camb = "00080300001"

		#file_ple = open(direccion_ple + 'LE' + ruc + self.period_ini.code[3:7]+ self.period_ini.code[:2]+name_camb+('1' if len(exp) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt','w')
		# file_ple.write(exp)
		# file_ple.close()

		vals = {
			'output_name': 'LE' + ruc + self.period_ini.code[3:7] + self.period_ini.code[:2]+name_camb+('1' if len(exp) > 0 else '0') + ('1' if mond == 'PEN' else '2') + '1.txt',
			'output_file': base64.encodestring("== Sin Registros ==" if exp == "" else exp),
			'respetar': 1,
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

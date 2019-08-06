# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from openerp.osv import osv
import base64
from zipfile import ZipFile

class resumen_fe(models.Model):
	_name = 'resumen.fe'

	fecha = fields.Date('Fecha',required=True)
	motivo = fields.Selection([('1','Conexion a Internet'),('2','Falla Fluido Electrico'),('3','Desastres Naturales'),('4','Robo'),('5','Falla en el sistema de emisión electrónico'),('6','Ventas por emisores itinerantes'),('7','Otros')],'Motivo',required=True)
	nro_correlativo = fields.Char('Correlativo',size=2,required=True)
	enviado = fields.Boolean('Enviado a Sunat')

	@api.onchange('nro_correlativo')
	def onchange_nro_correlativo(self):
		if self.nro_correlativo and len(self.nro_correlativo)== 1:
			self.nro_correlativo = '0'+ self.nro_correlativo

	@api.multi
	def do_rebuild(self):

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if True:
			self.env.cr.execute("""
			COPY (select 
			'""" +self.motivo+ """' as campo1,
			'01'::varchar as campo2,
			'""" +self.fecha.split('-')[2] + '/' + self.fecha.split('-')[1] + '/' + self.fecha.split('-')[0] + """' as campo3,
			venta.tipodocumento as campo4,
CASE WHEN			venta.serie is not Null THEN repeat('0',4-char_length(venta.serie)) || venta.serie ELSE '' END as campo5,
			CASE WHEN venta.numero is not Null THEN venta.numero ELSE '' END as campo6,
			''::varchar as campo7,
			
CASE WHEN (anulado.name = venta.partner and anulado.nro_documento = venta.numdoc) or (ventaboleta.name = venta.partner and ventaboleta.nro_documento = venta.numdoc) THEN '0' ELSE
CASE WHEN venta.tipodoc is not Null THEN venta.tipodoc::varchar ELSE '' END end as campo8,

CASE WHEN (anulado.name = venta.partner and anulado.nro_documento = venta.numdoc) or (ventaboleta.name = venta.partner and ventaboleta.nro_documento = venta.numdoc) THEN '0' ELSE
CASE WHEN venta.numdoc is not Null THEN venta.numdoc ELSE '' END END as campo9,

CASE WHEN (anulado.name = venta.partner and anulado.nro_documento = venta.numdoc) or (ventaboleta.name = venta.partner and ventaboleta.nro_documento = venta.numdoc) THEN 
	CASE WHEN (anulado.name = venta.partner and anulado.nro_documento = venta.numdoc) THEN 'Anulado' ELSE 'Clientes Varios' END
 ELSE
CASE WHEN venta.partner is not Null THEN venta.partner ELSE '' END END as campo10,

CASE WHEN am.currency_id is not Null THEN (currency.name)::varchar ELSE 'PEN'::varchar END as campo16,

CASE WHEN venta.baseimp is not Null THEN (venta.baseimp)::varchar ELSE '0.00' END as campo12,
CASE WHEN venta.exonerado is not Null THEN (venta.exonerado )::varchar ELSE '0.00' END as campo13,
CASE WHEN venta.inafecto is not Null THEN (venta.inafecto)::varchar ELSE '0.00' END as campo14,
CASE WHEN venta.isc is not Null THEN (venta.isc)::varchar ELSE '0.00' END as campo15,

'0.00' as campo16,

CASE WHEN venta.igv is not Null THEN (venta.igv)::varchar ELSE '0.00' END as campo17,
CASE WHEN venta.otros is not Null THEN (venta.otros)::varchar ELSE '0.00' END as campo18,
CASE WHEN venta.total is not Null THEN (venta.total)::varchar ELSE '0.00' END as campo19,
CASE WHEN venta.tipodocmod is not Null THEN venta.tipodocmod ELSE '' END as campo20,
CASE WHEN venta.seriemod is not Null THEN repeat('0',4-char_length(venta.seriemod)) || venta.seriemod ELSE '' END as campo21,
CASE WHEN venta.numeromod is not Null THEN venta.numeromod ELSE '' END as campo22,
''::varchar  as campo23,
'0.00' as campo24,
'0.00' as campo25,
'0.00' as campo26,
'' as campo27

from get_venta_1_1_1(0,209501) venta
inner join account_period ap on ap.name = venta.periodo
inner join account_move am on am.id = venta.am_id
cross join main_parameter 
left join res_partner anulado on anulado.id = main_parameter.partner_null_id
left join res_partner ventaboleta on ventaboleta.id = main_parameter.partner_venta_boleta
left join res_currency currency on currency.id = am.currency_id
inner join account_journal aj on aj.id = am.journal_id
where am.date = '"""+ str(self.fecha) + """' 
and (anulado.name is null or (anulado.name != venta.partner and anulado.nro_documento != venta.numdoc))
and venta.serie in (select regexp_replace(it_invoice_serie.name,'[^0-9]', '','g') from it_invoice_serie where it_invoice_serie.manual = True)
order by venta.tipodocumento, venta.serie, venta.numero
) 
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
			

		#file_ple = open(direccion_ple + 'LE' + ruc + self.period.code[3:7]+ self.period.code[:2]+name_camb+('1' if len(exp) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt','w')
		#file_ple.write(exp)
		#file_ple.close()


		"""with ZipFile( direccion + 'ojo.zip','w') as myzip:
			myzip.writestr(ruc + '-RF-' + self.fecha.split('-')[2] + self.fecha.split('-')[1] + self.fecha.split('-')[0] + '-' + self.nro_correlativo  +'.txt',exp)
			myzip.close()

		expZip = "".join(open(str(direccion + 'ojo.zip'),'rb').readlines() )
		vals = {
			'output_name': ruc + '-RF-' + self.fecha.split('-')[2] + self.fecha.split('-')[1] + self.fecha.split('-')[0] + '-' + self.nro_correlativo  +'.zip',
			'output_file': base64.encodestring(  expZip ),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		result = {}
		view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		print sfs_id """

		vals = {
				'output_name': ruc + '-RF-' + self.fecha.split('-')[0] + self.fecha.split('-')[1] + self.fecha.split('-')[2] + '-' + self.nro_correlativo  +'.txt',
				'output_file': base64.encodestring(  "== Sin Registros ==" if exp =="" else exp ),		
			}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}
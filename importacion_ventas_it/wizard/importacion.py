# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint


class ventas_imp_cabecera_tmp(models.Model):
	_name = 'ventas.imp.cabecera.tmp'

	campo1 = fields.Char('col1')
	campo2 = fields.Char('col2')
	campo3 = fields.Char('col3')
	campo4 = fields.Char('col4')
	campo5 = fields.Char('col5')
	campo6 = fields.Char('col6')
	campo7 = fields.Char('col7')
	campo8 = fields.Char('col8')
	campo9 = fields.Char('col9')
	campo10 = fields.Char('col10')
	campo11 = fields.Char('col11')
	campo12 = fields.Char('col12')
	campo13 = fields.Char('col13')
	campo14 = fields.Char('col14')
	campo15 = fields.Char('col15')
	camporelleno = fields.Char('col16')

class ventas_imp_detalle_tmp(models.Model):
	_name = 'ventas.imp.detalle.tmp'

	campo1 = fields.Char('col1')
	campo2 = fields.Char('col2')
	campo3 = fields.Char('col3')
	campo4 = fields.Char('col4')
	campo5 = fields.Char('col5')
	campo6 = fields.Char('col6')
	campo7 = fields.Char('col7')
	campo8 = fields.Char('col8')
	campo9 = fields.Char('col9')
	campo10 = fields.Char('col10')
	campo11 = fields.Char('col11')
	campo12 = fields.Char('col12')
	campo13 = fields.Char('col13')
	campo14 = fields.Char('col14')
	campo15 = fields.Char('col15')
	campo16 = fields.Char('col16')
	campo17 = fields.Char('col17')
	campo18 = fields.Char('col18')
	camporelleno = fields.Char('col19')

class account_move(models.Model):
	_inherit = 'account.move'

	imp_venta_id = fields.Many2one('importacion.ventas','importacion ventas')

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	imp_venta_id = fields.Many2one('importacion.ventas','importacion ventas')


class importacion_ventas(models.Model):
	_name='importacion.ventas'

	fecha = fields.Date(u'Fecha de Importación',required=True)
	state             = fields.Selection([('1','Borrador'),('2','Por Importar'),('3','Importado'),('4','Anulado')],'Estado',readonly=True,default="1",copy=False)
	delimitador       = fields.Char('Delimitador', size=1, default=',')

	file_imp          = fields.Binary(u'Archivo importación detalle',required=True)
	file_head_imp     = fields.Binary(u'Archivo importación cabecera', required=True)
	
	file_sal_error  = fields.Binary('Archivo Paso 1 Errores',readonly=True)
	file_sal_error_head  = fields.Binary('Archivo Paso 1 Errores Cabecera',readonly=True)


	file_imp_text          = fields.Char(u'Archivo importación detalle text')
	file_head_imp_text     = fields.Char(u'Archivo importación cabecera text')

	period_id =fields.Many2one('account.period','Periodo',required=True)
	diario = fields.Many2one('account.journal','Diario',required=True)

	tienda = fields.Many2one('tienda.importadas','Tienda')
	sal_name1 = fields.Char('Name 1',default='Observaciones_cabecera.csv')
	sal_name2 = fields.Char('Name 2',default='Observaciones_detalle.csv')


	name = fields.Char('Nombre',compute="get_name_caja")

	@api.one
	def get_name_caja(self):
		if self.id:
			self.name = 'Importacion Venta -' + str(self.id)
		else:
			self.name = 'Importacion Borrador'

	@api.model
	def create(self, vals):
		if len( self.env['importacion.ventas'].search([('state','in',('1','2'))]) ) >0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Por Importar.')

		#if len(self.env['importacion.ventas'].search([('fecha','=',vals['fecha'])])):
		#	raise osv.except_osv("Alerta!", u"Ya existe una importación con la fecha "+vals['fecha'])
		t = super(importacion_ventas, self).create(vals)
		
				
		xl_compras =  self.env['importacion.ventas'].search([('fecha','=',t.fecha),('id','!=',t.id)])
		if len(xl_compras)>0:
			for i in xl_compras:
				if t.tienda.id and i.tienda.id == t.tienda.id:
					raise osv.except_osv("Alerta!", u"Ya existe una importación con la fecha "+t.fecha)
		return t

	@api.one
	def write(self,vals):
		if len( self.env['importacion.ventas'].search([('state','in',('1','2')),('id','!=',self.id)]) )	>0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Por Importar.')

		t = super(importacion_ventas, self).write(vals)
		self.refresh()
		
		
		#if 'fecha' in vals:
		#	if len(self.env['importacion.ventas'].search([('fecha','=',vals['fecha'])])) > 1:
		#		raise osv.except_osv("Alerta!", u"Ya existe una importación con la fecha "+vals['fecha'])
				
		xl_compras =  self.env['importacion.ventas'].search([('fecha','=',self.fecha),('id','!=',self.id)])
		if len(xl_compras)>0:
			for i in xl_compras:
				if self.tienda.id and i.tienda.id == self.tienda.id:
					raise osv.except_osv("Alerta!", u"Ya existe una importación con la fecha "+self.fecha)
		return t

	@api.one
	def unlink(self):
		
		if self.state != '1':
			raise osv.except_osv('Alerta!','No se puede eliminar una importación en proceso.')
		return super(importacion_ventas,self).unlink()



	@api.multi
	def primerpaso(self):
		
		#f_cab = self.file_head_imp_text[3:11]
		#f_det = self.file_imp_text[3:11]
		#f_imp = self.fecha.replace('-','').decode('unicode-escape')

		#if f_imp != f_cab or f_imp != f_det:
		#	raise osv.except_osv("Alerta!","La fecha del archivo de cabecera y detalle debe coincidir con al fecha de importación.")
		#if f_cab != f_det:
		#	raise osv.except_osv("Alerta!","La fecha del archivo de cabecera debe coincidir con la del detalle.")


		# #########################################  CABECERA  #########################################
		
		import time		
		import base64
		import codecs


		parametros = self.env['main.parameter'].search([])[0]

		cabe_v1 = base64.b64decode(self.file_head_imp)
		file_cv1 = open(parametros.dir_create_file + 'ivenv1p.csv','wb')
		file_cv1.write(cabe_v1)
		file_cv1.close()


		flag = False
		try:
			f = codecs.open(parametros.dir_create_file + 'ivenv1p.csv',encoding='utf-8',errors='strict')
			f.read()
		except UnicodeDecodeError:
			flag= True

		if flag:
			import codecs
			BLOCKSIZE = 1048576 # or some other, desired size in bytes
			with codecs.open(parametros.dir_create_file + 'ivenv1p.csv', "r", "iso-8859-1") as sourceFile:
				with codecs.open(parametros.dir_create_file + 'ivenv1.csv', "w", "utf-8") as targetFile:
					while True:
						contents = sourceFile.read(BLOCKSIZE)
						if not contents:
							break
						targetFile.write(contents)
		else:			
			file_cv1 = open(parametros.dir_create_file + 'ivenv1.csv','wb')
			file_cv1.write(cabe_v1)
			file_cv1.close()


		self.env.cr.execute("""
		delete from ventas_imp_cabecera_tmp;
		 """)

		try:
			self.env.cr.execute("""
			copy ventas_imp_cabecera_tmp (campo1,campo2,campo3,campo4,campo5,campo6,campo7,campo8,campo9,campo10,campo11,campo12,campo13,campo14,campo15,camporelleno) from '""" +parametros.dir_create_file + 'ivenv1.csv'+ """' with delimiter '"""+self.delimitador+"""' CSV ;
			 """)

		except Exception as e:
			raise osv.except_osv("Alerta!","El Archivo ha importar posiblemente no es el correcto o contiene en alguno de sus campos como parte de su información el separador: '"+ self.delimitador + "'."+ "\n\n"+ str(e))

		self.env.cr.execute("""
			drop table if exists ventas_imp_cabecera_tmp_v2;

			create table ventas_imp_cabecera_tmp_v2 AS (
				select campo1,campo2,campo3,campo4,campo5,campo6,campo7,campo8,campo9,campo10,campo11,campo12,campo13,campo14,campo15, rp.id as campo16,
				itd.id as campo17, rc.id as campo18, itd_mod.id as campo19 , coalesce(itd.code,'ND') || '-' || campo3 as campo20
				from ventas_imp_cabecera_tmp cv1
				left join res_partner rp on rp.nro_documento = campo2
				left join einvoice_catalog_01 itd on itd.code = campo5
				left join res_currency rc on rc.name = campo8
				left join einvoice_catalog_01 itd_mod on itd_mod.code = campo9
				where campo5 not in ('0','00')
			);
		 """)

		self.env.cr.execute("""
			copy (
			select distinct
				case when campo16 is null then 'No existe el Partner: ' || coalesce(campo2,'') else '-' end as ver_partner,
				case when campo17 is null then 'No existe el Tipo Documento: ' || coalesce(campo5,'') else '-' end as ver_tipo_doc
			from ventas_imp_cabecera_tmp_v2 where campo16 is null or campo17 is null
				)	
			TO '"""+ str( parametros.dir_create_file + 'ivenv2.csv' )+ """'
			with delimiter '|'  CSV 

		 """)

		exp = open(str( parametros.dir_create_file + 'ivenv2.csv' ),'r' ).read()

		self.file_sal_error_head  = base64.encodestring(exp)





		# #########################################  DETALLE  #########################################
		
		import time		
		import base64
		import codecs


		parametros = self.env['main.parameter'].search([])[0]

		cabe_v1 = base64.b64decode(self.file_imp)
		file_cv1 = open(parametros.dir_create_file + 'divenv1p.csv','wb')
		file_cv1.write(cabe_v1)
		file_cv1.close()


		flag = False
		try:
			f = codecs.open(parametros.dir_create_file + 'divenv1p.csv',encoding='utf-8',errors='strict')
			f.read()
		except UnicodeDecodeError:
			flag= True

		if flag:
			import codecs
			BLOCKSIZE = 1048576 # or some other, desired size in bytes
			with codecs.open(parametros.dir_create_file + 'divenv1p.csv', "r", "iso-8859-1") as sourceFile:
				with codecs.open(parametros.dir_create_file + 'divenv1.csv', "w", "utf-8") as targetFile:
					while True:
						contents = sourceFile.read(BLOCKSIZE)
						if not contents:
							break
						targetFile.write(contents)
		else:			
			file_cv1 = open(parametros.dir_create_file + 'divenv1.csv','wb')
			file_cv1.write(cabe_v1)
			file_cv1.close()


		self.env.cr.execute("""
		delete from ventas_imp_detalle_tmp;
		 """)

		try:
			self.env.cr.execute("""
			copy ventas_imp_detalle_tmp (campo1,campo2,campo3,campo4,campo5,campo6,campo7,campo8,campo9,campo10,campo11,campo12,campo13,campo14,campo15,campo16,campo17,campo18,camporelleno) from '""" +parametros.dir_create_file + 'divenv1.csv'+ """' with delimiter '"""+self.delimitador+"""' CSV ;
			 """)

		except Exception as e:
			raise osv.except_osv("Alerta!","El Archivo ha importar posiblemente no es el correcto o contiene en alguno de sus campos como parte de su información el separador: '"+ self.delimitador + "'."+ "\n\n"+ str(e))

		self.env.cr.execute("""
			drop table if exists ventas_imp_detalle_tmp_v2;

			create table ventas_imp_detalle_tmp_v2 AS (
				select campo1,campo2,campo3,campo4,campo5,campo6,campo7,campo8,campo9,campo10,campo11,campo12,campo13,campo14,campo15,campo16,campo17,campo18,
				rp.id as campo19,
				pp.id as campo20,
				aa.id as campo21,
				aaa.id as campo22,
				atc.id as campo23,
				itd.id as campo24,
				pu.id as campo25,
				rc.id as campo26,
				coalesce(itd.code,'ND') || '-' || campo3 as campo27
				from ventas_imp_detalle_tmp cv1
				left join res_partner rp on rp.nro_documento = campo2
				left join product_product pp on pp.default_code = campo4
				left join account_account aa on aa.code = campo5
				left join account_analytic_account aaa on aaa.code = campo9
				left join account_tax_code atc on atc.code = campo12
				left join einvoice_catalog_01 itd on itd.code = campo15
				left join product_uom pu on pu.name = campo17				
				left join res_currency rc on rc.name = campo11 and rc.name != 'PEN'
				where campo15 not in ('0','00')
			);
		 """)

		self.env.cr.execute("""
			copy (
			select distinct
				case when campo21 is null then 'No existe la Cuenta Contable: ' || coalesce(campo5,'') else '-' end as ver_partner,
				case when campo24 is null then 'No existe el Tipo Documento: ' || coalesce(campo15,'') else '-' end as ver_partner
			from ventas_imp_detalle_tmp_v2 where campo21 is null or campo24 is null
				)	
			TO '"""+ str( parametros.dir_create_file + 'divenv2.csv' )+ """'
			with delimiter '|'  CSV 

		 """)

		exp = open(str( parametros.dir_create_file + 'divenv2.csv' ),'r' ).read()

		self.file_sal_error  = base64.encodestring(exp)


		if self.file_sal_error_head or self.file_sal_error:
			pass
		else:
			self.state = '2'


	@api.one
	def segundopaso(self):
		
		

		#########################################  Cabecera  #########################################
		import time		
		import base64


		self.env.cr.execute(""" 
			INSERT INTO account_move(fecha_contable,partner_id,date,ple_venta,name,state,journal_id,ref,company_id,ple_diariomayor, imp_venta_id,fecha_special) 
			select distinct (split_part(campo1::varchar,'/'::varchar,2)::varchar || '-'::varchar ||  split_part(campo1::varchar,'/'::varchar,1)::varchar || '-01'::varchar )::date,campo16,campo4::date,campo15, campo20 ,'posted',"""+str(self.diario.id)+""", campo20 ,1, '1',"""+str(self.id)+""",false  from ventas_imp_cabecera_tmp_v2;		

		""")

		
		self.env.cr.execute("""
			INSERT INTO account_invoice(number,partner_id,it_type_document,reference,currency_id,date_invoice,journal_id, move_id,company_id,account_id,reference_type,type,state,imp_venta_id)
			select distinct campo3, campo16, campo17,campo3, CASE WHEN campo18 is not null then campo18 else (select id from res_currency where name = 'PEN') end, campo4::date, """+str(self.diario.id)+""",  am.id,1,4592,'none','out_invoice','paid',"""+str(self.id)+ """  from ventas_imp_cabecera_tmp_v2
			inner join account_move am on am.imp_venta_id = """+str(self.id)+ """ and am.name = campo20;
			""")

		self.env.cr.execute("""
			INSERT INTO account_perception(tipo_doc,fecha,comprobante,father_invoice_id,perception,base_imponible,igv)
			select campo19,campo11::date,campo10, ai.id ,campo14::numeric,campo12::numeric,campo13::numeric from ventas_imp_cabecera_tmp_v2
			inner join account_invoice ai on ai.number = ventas_imp_cabecera_tmp_v2.campo3 and ai.imp_venta_id = """ +str(self.id)+"""
			where campo11 is not null;		
			""")


		self.env.cr.execute(""" 
			INSERT INTO account_move_line(name,partner_id,nro_comprobante,product_id,account_id,date_maturity,debit,credit,analytic_account_id,amount_currency,currency_id,tax_code_id,tax_amount,tc,type_document_it,quantity,product_uom_id,journal_id,date, move_id,company_id) 
			select campo1,campo19,campo3,campo20,campo21,campo6::date,campo7::numeric,campo8::numeric,campo22,campo10::numeric,campo26,campo23,campo13::numeric,campo14::numeric,campo24,campo16::numeric,campo25,am.journal_id,am.date,am.id,1  from ventas_imp_detalle_tmp_v2
			inner join account_move am on am.name = ventas_imp_detalle_tmp_v2.campo27 and am.imp_venta_id = """ +str(self.id)+ """;		
		""")

		
		self.env.cr.execute(""" 
		UPDATE account_move set
		partner_id = T.partner_id
		from (
			select am.id as id, max(aml.partner_id )  as partner_id  from account_move am
			inner join account_move_line aml on aml.move_id = am.id
			inner join account_journal aj on aj.id = am.journal_id and aj.id = """ +str(self.diario.id)+ """
			where am.partner_id is null
			group by am.id
			order by am.id
		) T
		where T.id = account_move.id and account_move.journal_id = """ +str(self.diario.id)+ """
		""")

		self.state = '3'


		#########################################  CABECERA  #########################################
		



	@api.multi
	def anular_importacion(self):
		self.env.cr.execute(""" 
			delete from account_perception where father_invoice_id in (select id from account_invoice where imp_venta_id = """+str(self.id)+""")
			""")

		self.env.cr.execute(""" 
			delete from account_invoice where move_id in (select id from account_move where imp_venta_id = """+str(self.id)+""")
			""")
		
		self.env.cr.execute(""" 
			delete from account_move_line where move_id in (select id from account_move where imp_venta_id = """+str(self.id)+""")
			""")

		self.env.cr.execute(""" 
			delete from account_move where id in (select id from account_move where imp_venta_id = """+str(self.id)+""")
			""")
		self.state = '4'



	@api.one
	def regresar_borrador(self):
		
		self.state = '1'
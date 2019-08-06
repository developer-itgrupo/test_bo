# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class timport_caja_cabecera_v1(models.Model):
	_name = 'timport.caja.cabecera.v1'

	campo1 = fields.Char('Campo1')
	campo2 = fields.Char('Campo2')
	campo3 = fields.Char('Campo3')
	campo4 = fields.Char('Campo4')
	campo5 = fields.Char('Campo5')
	campo6 = fields.Char('Campo6')
	campo7 = fields.Char('Campo7')
	campo8 = fields.Char('Campo8')
	campo9 = fields.Char('Campo9')
	campo10 = fields.Char('Campo10')
	camporelleno = fields.Char('Campo9')


class timport_caja_detalle_v1(models.Model):
	_name = 'timport.caja.detalle.v1'

	campo1 = fields.Char('Campo1')
	campo2 = fields.Char('Campo2')
	campo3 = fields.Char('Campo3')
	campo4 = fields.Char('Campo4')
	campo5 = fields.Char('Campo5')
	campo6 = fields.Char('Campo6')
	campo7 = fields.Char('Campo7')
	campo8 = fields.Char('Campo8')
	campo9 = fields.Char('Campo9')
	campo10 = fields.Char('Campo10')
	campo11 = fields.Char('Campo11')
	campo12 = fields.Char('Campo12')
	camporelleno = fields.Char('Campo9')


class account_move(models.Model):
	_inherit = 'account.move'

	cod_tienda = fields.Char('Codigo Tienda')
	cod_caja = fields.Char('Codigo Caja')
	import_caja_id = fields.Integer('IC_id')


class importacion_caja(models.Model):
	_name='importacion.caja'

	fecha = fields.Date('Fecha')

	file_imp = fields.Binary('Archivo Importacion',required=True)
	file_head_imp = fields.Binary('Archivo importación cabecera', required=True)
	
	file_sal_primer = fields.Binary('Archivo Paso 1',readonly=True)
	file_sal_error = fields.Binary('Archivo Paso 1 Errores',readonly=True,copy=False)

	file_sal_primer_head = fields.Binary('Archivo Paso 1 Cabecera',readonly=True)
	file_sal_error_head = fields.Binary('Archivo Paso 1 Errores Cabecera',readonly=True,copy=False)
	
	
	delimitador = fields.Char('Delimitador', size=1, default=',')

	period_id =fields.Many2one('account.period','Periodo',required=True)
	diario =fields.Many2one('account.journal','Diario',required=True)
	
	sal_name1 = fields.Char('Name 1',default='Observacion_cabecera.csv')
	sal_name2 = fields.Char('Name 2',default='Observacion_detalle.csv')

	n_cabecera = fields.Char('Name 1')
	n_detalle = fields.Char('Name 2')
	
	glosa = fields.Char('Glosa')
	
	state = fields.Selection([('1','Borrador'),('2','Por Importar'),('3','Importado'),('4','Anulado')],'Estado',readonly=True,default="1",copy=False)

	name = fields.Char('Nombre',compute="get_name_caja")

	@api.one
	def get_name_caja(self):
		if self.id:
			self.name = 'Importacion C-' + str(self.id)
		else:
			self.name = 'Importacion Borrador'


	@api.model
	def create(self,vals):	
		if len( self.env['importacion.caja'].search([('state','in',('1','2'))]) ) >0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Por Importar.')
		t = super(importacion_caja,self).create(vals)
		t.refresh()

		# permiso = self.env['account.journal.period'].search([('period_id','=',t.period_id.id),('journal_id','=',t.diario.id)])
		# if len(permiso)>0 and permiso[0].state != 'draft':
		# 	raise osv.except_osv('Alerta!','El Periodo para el diario esta cerrado.')
		#otros = self.env['importacion.caja'].search([('id','!=',t.id),('fecha','=',t.fecha)])
		#if len(otros)>0:
		#	raise osv.except_osv('Alerta!','Ya existe una importación para esa fecha.')
		return t

	@api.one
	def write(self,vals):
		if len( self.env['importacion.caja'].search([('state','in',('1','2')),('id','!=',self.id)]) )	>0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Por Importar.')

		t = super(importacion_caja,self).write(vals)
		self.refresh()
		# permiso = self.env['account.journal.period'].search([('period_id','=',self.period_id.id),('journal_id','=',self.diario.id)])
		# if len(permiso)>0 and permiso[0].state != 'draft':
		# 	raise osv.except_osv('Alerta!','El Periodo para el diario esta cerrado.')

		#otros = self.env['importacion.caja'].search([('id','!=',self.id),('fecha','=',self.fecha)])
		#if len(otros)>0:
		#	raise osv.except_osv('Alerta!','Ya existe una importación para esa fecha.')
		return t

	@api.one
	def unlink(self):
		# permiso = self.env['account.journal.period'].search([('period_id','=',self.period_id.id),('journal_id','=',self.diario.id)])
		# if len(permiso)>0 and permiso[0].state != 'draft':
		# 	raise osv.except_osv('Alerta!','El Periodo para el diario esta cerrado.')

		if self.state != '1':
			raise osv.except_osv('Alerta!','No se puede eliminar una importación en proceso.')
		return super(importacion_caja,self).unlink()

	@api.multi
	def eliminarImportacion(self):
		
		# permiso = self.env['account.journal.period'].search([('period_id','=',self.period_id.id),('journal_id','=',self.diario.id)])
		# if len(permiso)>0 and permiso[0].state != 'draft':
		# 	raise osv.except_osv('Alerta!','El Periodo para el diario esta cerrado.')

		# if self.period_id.state != 'draft':
		# 	raise osv.except_osv('Alerta!','El Periodo esta cerrado.')

		self.env.cr.execute(""" 
			delete from account_move_line where move_id in (select id from account_move where import_caja_id = """+str(self.id)+""")
			""")

		self.env.cr.execute(""" 
			delete from account_move where id in (select id from account_move where import_caja_id = """+str(self.id)+""")
			""")
		self.state = '4'



	@api.multi
	def primerpaso(self):	
		# permiso = self.env['account.journal.period'].search([('period_id','=',self.period_id.id),('journal_id','=',self.diario.id)])
		# if len(permiso)>0 and permiso[0].state != 'draft':
		# 	raise osv.except_osv('Alerta!','El Periodo para el diario esta cerrado.')


		#########################################  CABECERA  #########################################
		import time		
		import base64
		import codecs


		parametros = self.env['main.parameter'].search([])[0]

		cabe_v1 = base64.b64decode(self.file_head_imp)
		file_cv1 = open(parametros.dir_create_file + 'icv1p.csv','wb')
		file_cv1.write(cabe_v1)
		file_cv1.close()


		flag = False
		try:
			f = codecs.open(parametros.dir_create_file + 'icv1p.csv',encoding='utf-8',errors='strict')
			f.read()
		except UnicodeDecodeError:
			flag= True

		if flag:
			import codecs
			BLOCKSIZE = 1048576 # or some other, desired size in bytes
			with codecs.open(parametros.dir_create_file + 'icv1p.csv', "r", "iso-8859-1") as sourceFile:
				with codecs.open(parametros.dir_create_file + 'icv1.csv', "w", "utf-8") as targetFile:
					while True:
						contents = sourceFile.read(BLOCKSIZE)
						if not contents:
							break
						targetFile.write(contents)
		else:			
			file_cv1 = open(parametros.dir_create_file + 'icv1.csv','wb')
			file_cv1.write(cabe_v1)
			file_cv1.close()


		self.env.cr.execute("""
		delete from timport_caja_cabecera_v1;
		 """)

		try:
			self.env.cr.execute("""
			copy timport_caja_cabecera_v1 (campo1,campo2,campo3,campo4,campo5,campo6,campo7,campo8,campo9,campo10) from '""" +parametros.dir_create_file + 'icv1.csv'+ """' with delimiter '"""+self.delimitador+"""' CSV ;
			 """)
		except Exception as e:
			raise osv.except_osv("Alerta!","El Archivo ha importar posiblemente no es el correcto o contiene en alguno de sus campos como parte de su información el separador: '"+ self.delimitador + "'."+ "\n\n"+ str(e))

		self.env.cr.execute("""
			drop table if exists timport_caja_cabecera_v2;

			create table timport_caja_cabecera_v2 AS (
				select campo1,campo2,campo3,campo4,campo5,campo6,campo7,campo8,campo9, rp.id as campo10, itd.id as campo11, cv1.campo10 as campo12, imp.id as campo13  from timport_caja_cabecera_v1 cv1
				left join res_partner rp on rp.nro_documento = cv1.campo8
				left join einvoice_catalog_01 itd on itd.code = cv1.campo7 
				left join einvoice_means_payment imp on imp.code = cv1.campo10
			);
		 """)

		self.env.cr.execute("""
			copy (
			select distinct
				case when campo10 is null then 'No existe el Partner: ' || coalesce(campo8,'') else '-' end as ver_partner
				--case when campo11 is null then 'No existe el Tipo Documento: ' || coalesce(campo7,'') else '-' end as ver_tipo_doc
			from timport_caja_cabecera_v2 where campo10 is null
				)	
			TO '"""+ str( parametros.dir_create_file + 'icv2.csv' )+ """'
			with delimiter '|'  CSV 

		 """)

		exp = open(str( parametros.dir_create_file + 'icv2.csv' ),'r' ).read()

		#	tmp +=  lineas[0] +"|"+ id_periodo+"|"+lineas[2]+"|"+lineas[3]+"|"+lineas[4]+"|"+lineas[5]+"|"+id_tipo_doc+"|"+id_partner+"\n"
		self.file_sal_error_head  = base64.encodestring(exp)


		##################################### detalle ###########################################


		import codecs

		det_v1 = base64.b64decode(self.file_imp)
		file_dv1 = open(parametros.dir_create_file + 'idv1p.csv','wb')
		file_dv1.write(det_v1)
		file_dv1.close()


		flag = False
		try:
			f = codecs.open(parametros.dir_create_file + 'idv1p.csv',encoding='utf-8',errors='strict')
			f.read()
		except UnicodeDecodeError:
			flag= True

		if flag:
			import codecs
			BLOCKSIZE = 1048576 # or some other, desired size in bytes
			with codecs.open(parametros.dir_create_file + 'idv1p.csv', "r", "iso-8859-1") as sourceFile:
				with codecs.open(parametros.dir_create_file + 'idv1.csv', "w", "utf-8") as targetFile:
					while True:
						contents = sourceFile.read(BLOCKSIZE)
						if not contents:
							break
						targetFile.write(contents)
		else:			
			file_cv1 = open(parametros.dir_create_file + 'idv1.csv','wb')
			file_cv1.write(det_v1)
			file_cv1.close()


		self.env.cr.execute("""
		delete from timport_caja_detalle_v1;
		 """)

		try:
			self.env.cr.execute("""
			copy timport_caja_detalle_v1 (campo1,campo2,campo3,campo4,campo5,campo6,campo7,campo8,campo9,campo10,campo11,campo12,camporelleno) from '""" +parametros.dir_create_file + 'idv1.csv'+ """' with delimiter '"""+self.delimitador+"""' CSV ;
			 """)
		except Exception as e:			
			raise osv.except_osv("Alerta!","El Archivo ha importar posiblemente no es el correcto o contiene en alguno de sus campos como parte de su información el separador: '"+ self.delimitador + "'."+ "\n\n"+ str(e))


		self.env.cr.execute("""
			drop table if exists timport_caja_detalle_v2;

			create table timport_caja_detalle_v2 AS (
				select campo1,campo2,campo3,campo4,campo5,campo6,campo7,campo8,campo9,campo10,campo11,campo12, rp.id as campo13,
				itd.id as campo14, imp.id as campo15, rc.id as campo16, aa.id as campo17, aaa.id as campo18 from timport_caja_detalle_v1 dv1
				left join res_partner rp on rp.nro_documento = dv1.campo3
				left join einvoice_catalog_01 itd on itd.code = dv1.campo4
				left join einvoice_means_payment imp on imp.code = dv1.campo12
				left join res_currency rc on rc.name = dv1.campo11 and rc.name != 'PEN'
				left join account_account aa on aa.code = dv1.campo6
				left join account_analytic_account aaa on aaa.code = dv1.campo9
			);
		 """)

		self.env.cr.execute("""
			copy (
			select distinct
				case when campo13 is null then 'No existe el Partner: ' || coalesce(campo3,'') else '-' end as ver_partner,
				case when campo14 is null then 'No existe el Tipo Documento: ' || coalesce(campo4,'') else '-' end as ver_tipo_doc,
				--case when campo16 is null then 'No existe el Moneda: ' || coalesce(campo11,'') else '-' end as ver_moneda,
				case when campo17 is null then 'No existe el Cuenta Contable: ' || coalesce(campo6,'') else '-' end as ver_cuenta_contable
				--case when campo18 is null then 'No existe el Cuenta Analitica: ' || coalesce(campo9,'') else '-' end as ver_cuenta_analitica
			from timport_caja_detalle_v2 where campo13 is null or campo14 is null or campo17 is null 
				)	
			TO '"""+ str( parametros.dir_create_file + 'idv2.csv' )+ """'
			with delimiter '|'  CSV 
		 """)

		exp = open(str( parametros.dir_create_file + 'idv2.csv' ),'r' ).read()

		self.file_sal_error  = base64.encodestring(exp)

		
		#################################################################################################

		if self.file_sal_error_head or self.file_sal_error:
			pass
		else:
			self.state = '2'

	@api.one
	def regresar_borrador(self):
		# permiso = self.env['account.journal.period'].search([('period_id','=',self.period_id.id),('journal_id','=',self.diario.id)])
		# if len(permiso)>0 and permiso[0].state != 'draft':
		# 	raise osv.except_osv('Alerta!','El Periodo para el diario esta cerrado.')

		self.state = '1'

	@api.one
	def segundopaso(self):
		# permiso = self.env['account.journal.period'].search([('period_id','=',self.period_id.id),('journal_id','=',self.diario.id)])
		# if len(permiso)>0 and permiso[0].state != 'draft':
		# 	raise osv.except_osv('Alerta!','El Periodo para el diario esta cerrado.')

		if self.period_id.state == 'done':
			raise osv.except_osv("Alerta!","El periodo "+self.period_id.code+u" está cerrado.") 

		#########################################  Cabecera  #########################################
		import time		
		import base64


		self.env.cr.execute(""" 
			INSERT INTO account_move(fecha_contable,partner_id,date,name,state,journal_id,ref,company_id,cod_tienda,cod_caja,ple_diariomayor,import_caja_id, means_payment_it) 
			select campo3::date,campo10,campo3::date,campo1,'posted',"""+str(self.diario.id)+""",'Importacion-c"""+str(self.id)+"""',1,campo4,campo5,'1',"""+str(self.id)+""" , campo13 from timport_caja_cabecera_v2;		
		""")

		

		self.env.cr.execute(""" 
			INSERT INTO account_move_line(name,partner_id,nro_comprobante,account_id,debit,credit,analytic_account_id,amount_currency,currency_id,type_document_it,journal_id,date, move_id,company_id,date_maturity) 
			select campo1,campo13,campo5,campo17,campo7::numeric,campo8::numeric,campo18,campo10::numeric,campo16,campo14,am.journal_id,am.date,am.id,1,am.date  from timport_caja_detalle_v2
			inner join account_move am on am.name = timport_caja_detalle_v2.campo1 and am.import_caja_id = """ +str(self.id)+ """;		
		""")



		self.env.cr.execute(""" 
			UPDATE ACCOUNT_MOVE SET amount = (select sum(debit) from account_move_line where move_id = ACCOUNT_MOVE.id )
			where import_caja_id = """ +str(self.id)+ """;		
		""")

		self.state = '3'

# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint
import codecs

class unidad_medida_imp_tmp(models.Model):
	_name = 'unidades.imp.medida.tmp'

	campo1 = fields.Char('col1')
	campo2 = fields.Integer('col2')
	campo3 = fields.Char('col3')
	campo4 = fields.Char('col4')
	camporelleno = fields.Char('col5')


class importacion_partner_i(models.Model):
	_name='importacion.unidad.medi.i'

	state             = fields.Selection([('1','Borrador'),('2','Por Importar'),('3','Importado')],'Estado',readonly=True,default="1",copy=False)
	delimitador       = fields.Char('Delimitador', size=1, default=',')

	file_unit_imp = fields.Binary(u'Archivo importación unidades', required=True)
	file_sal_error_partner = fields.Binary('Productos Paso 1 Errores', readonly=True,copy=False)

	period_id =fields.Many2one('account.period','Periodo',required=True)
	fecha = fields.Date('Fecha de Importacion')

	sal_name1 = fields.Char('Name 1',default='Observaciones_cliente_proveedor.csv')
	
	file_partner_imp_text = fields.Char(u'Archivo importación productos text')
	glosa = fields.Char('Glosa')
	_name_rec = 'fecha'


	@api.model
	def create(self, vals):
		if len( self.env['importacion.unidad.medi.i'].search([('state','in',('1','2'))]) ) >0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Por Importar.')

		#if len( self.env['importacion.partner.i'].search([('fecha','=',vals['fecha'])])):
		#	raise osv.except_osv("Alerta!", u"Ya existe una importación con la fecha "+vals['fecha'])
		t = super(importacion_partner_i, self).create(vals)
		return t

	@api.one
	def write(self,vals):
		if len( self.env['importacion.unidad.medi.i'].search([('state','in',('1','2')),('id','!=',self.id)]) )	>0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Por Importar.')

		t = super(importacion_partner_i, self).write(vals)
		self.refresh()
		
		#if 'fecha_importación' in vals:
		#	if len(self.env['importacion.partner.i'].search([('fecha','=',vals['fecha'])])) > 1:
		#		raise osv.except_osv("Alerta!", u"Ya existe una importación con la fecha "+vals['fecha'])
				
		return t

	@api.one
	def unlink(self):
		if self.state == '3':
			raise osv.except_osv("Alerta!","La importación está finalizada.")
		return super(importacion_partner_i,self).unlink()


	@api.multi
	def primerpaso(self):
		#########################################  PARTNER  #########################################

		import time		
		import base64
		import codecs



		parametros = self.env['main.parameter'].search([])[0]

		categoria = self.env['product.uom.categ']

		cabe_v1 = base64.b64decode(self.file_unit_imp)
		file_cv1 = open(parametros.dir_create_file + 'iparv1p.csv','wb')
		file_cv1.write(cabe_v1)
		file_cv1.close()


		flag = False
		try:
			f = codecs.open(parametros.dir_create_file + 'iparv1p.csv',encoding='utf-8',errors='strict')
			f.read()
		except UnicodeDecodeError:
			flag= True

		if flag:
			import codecs
			BLOCKSIZE = 1048576 # or some other, desired size in bytes
			with codecs.open(parametros.dir_create_file + 'iparv1p.csv', "r", "iso-8859-1") as sourceFile:
				with codecs.open(parametros.dir_create_file + 'iparv1.csv', "w", "utf-8") as targetFile:
					while True:
						contents = sourceFile.read(BLOCKSIZE)
						if not contents:
							break
						targetFile.write(contents)
		else:			
			file_cv1 = open(parametros.dir_create_file + 'iparv1.csv','wb')
			file_cv1.write(cabe_v1)
			file_cv1.close()


		self.env.cr.execute("""
		delete from unidades_imp_medida_tmp;
		 """)

		try:
			self.env.cr.execute("""
			copy unidades_imp_medida_tmp (campo1,campo2,campo3,campo4,camporelleno) from '""" +parametros.dir_create_file + 'iparv1.csv'+ """' with delimiter '"""+(self.delimitador).encode("utf-8")+"""' CSV ;
			 """)

		except Exception as e:
			raise osv.except_osv("Alerta!","El Archivo ha importar posiblemente no es el correcto o contiene en alguno de sus campos como parte de su información el separador: '"+ (self.delimitador).encode("utf-8") + "'." + "\n\n"+ str(e))

		self.env.cr.execute("""
			drop table if exists unidades_imp_medida_tmp_v2;

			create table unidades_imp_medida_tmp_v2 AS (
				select campo1,campo2,campo3,campo4, rp.id as campo5
				 from unidades_imp_medida_tmp otm
				left join product_uom rp on rp.name = otm.campo1
			);
		 """)



		self.env.cr.execute("""
			copy (
			select distinct
				case when campo1 is null then 'No contiene numero: ' || coalesce(campo2,'') else '-' end as codigo,
				case when campo2 is null then 'No contiene nombre: ' || coalesce(campo1,'') else '-' end as codigo
			from ventas_imp_clientes_tmp_v2 where campo1 is null or campo2 is null
				)	
			TO '"""+ str( parametros.dir_create_file + 'iparv2.csv' )+ """'
			with delimiter '|'  CSV 

		 """)

		exp = open(str( parametros.dir_create_file + 'iparv2.csv' ),'r' ).read()

		self.file_sal_error_partner  = base64.encodestring(exp)


		if self.file_sal_error_partner:
			pass
		else:
			self.state = '2'

	@api.one
	def regresar_borrador(self):
		self.state = '1'

	@api.one
	def segundopaso(self):

		#########################################  Cabecera  #########################################
		import time		
		import base64
		
		self.env.cr.execute(""" 
			INSERT INTO product_uom (name,category_id,uom_type,rounding,active,factor)
			select campo1,CAST(campo2 AS INTEGER),'reference',cast(campo4 AS float),true,1.0  from unidades_imp_medida_tmp_v2 where campo5 is null;
		""")

		self.state = '3' 


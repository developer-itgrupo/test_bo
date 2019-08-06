# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint
import codecs

class ventas_imp_productos_tmp(models.Model):
	_name = 'ventas.imp.productos.tmp'

	campo1 = fields.Char('col1')
	campo2 = fields.Char('col2')
	campo3 = fields.Char('col3')
	campo4 = fields.Char('col4')
	campo5 = fields.Char('col5')
	camporelleno = fields.Char('col6')

class importacion_producto_i(models.Model):
	_name='importacion.producto.i'

	state             = fields.Selection([('1','Borrador'),('2','Por Importar'),('3','Importado')],'Estado',readonly=True,default="1",copy=False)
	delimitador       = fields.Char('Delimitador', size=1, default=',')

	file_producto_imp = fields.Binary(u'Archivo importación productos', required=True)
	file_sal_error_producto = fields.Binary('Productos Paso 1 Errores', readonly=True,copy=False)

	period_id =fields.Many2one('account.period','Periodo',required=True)
	fecha = fields.Date('Fecha de Importacion')

	sal_name1 = fields.Char('Name 1',default='Observaciones_productos.csv')
	glosa = fields.Char('Glosa')
	file_producto_imp_text = fields.Char(u'Archivo importación productos text')

	_name_rec = 'fecha'


	@api.model
	def create(self, vals):
		if len( self.env['importacion.producto.i'].search([('state','in',('1','2'))]) ) >0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Por Importar.')

		#if len( self.env['importacion.producto.i'].search([('fecha','=',vals['fecha'])])):
		#	raise osv.except_osv("Alerta!", u"Ya existe una importación con la fecha "+vals['fecha'])
		t = super(importacion_producto_i, self).create(vals)
		return t

	@api.one
	def write(self,vals):
		if len( self.env['importacion.producto.i'].search([('state','in',('1','2')),('id','!=',self.id)]) )	>0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Por Importar.')

		t = super(importacion_producto_i, self).write(vals)
		self.refresh()
		
		#if 'fecha_importación' in vals:
		#	if len(self.env['importacion.producto.i'].search([('fecha','=',vals['fecha'])])) > 1:
		#		raise osv.except_osv("Alerta!", u"Ya existe una importación con la fecha "+vals['fecha'])
				
		return t

	@api.one
	def unlink(self):
		if self.state == '3':
			raise osv.except_osv("Alerta!","La importación está finalizada.")
		return super(importacion_producto_i,self).unlink()


	@api.multi
	def primerpaso(self):
		if len(self.env['product.category'].search([('codigo_categoria','=','SC')])) == 0:
			raise osv.except_osv("Alerta!","Debe crear una categoría denominada 'SIN CATEGORIA' con código 'SC' para los nuevos productos .")

		#########################################  PRODUCTOS  #########################################

		import time		
		import base64
		import codecs


		parametros = self.env['main.parameter'].search([])[0]

		cabe_v1 = base64.b64decode(self.file_producto_imp)

		file_cv1 = open(parametros.dir_create_file + 'iprv1p.csv','wb')
		file_cv1.write(cabe_v1)
		file_cv1.close()

		flag = False
		try:
			f = codecs.open(parametros.dir_create_file + 'iprv1p.csv',encoding='utf-8',errors='strict')
			f.read()
		except UnicodeDecodeError:
			flag= True

		if flag:
			import codecs
			BLOCKSIZE = 1048576 # or some other, desired size in bytes
			with codecs.open(parametros.dir_create_file + 'iprv1p.csv', "r", "iso-8859-1") as sourceFile:
				with codecs.open(parametros.dir_create_file + 'iprv1.csv', "w", "utf-8") as targetFile:
					while True:
						contents = sourceFile.read(BLOCKSIZE)
						if not contents:
							break
						targetFile.write(contents)
		else:			
			file_cv1 = open(parametros.dir_create_file + 'iprv1.csv','wb')
			file_cv1.write(cabe_v1)
			file_cv1.close()

		self.env.cr.execute("""
		delete from ventas_imp_productos_tmp;
		 """)

		try:

			self.env.cr.execute("""
			copy ventas_imp_productos_tmp (campo1,campo2,campo3,campo4,campo5,camporelleno) from '""" +parametros.dir_create_file + 'iprv1.csv'+ """' with delimiter '"""+self.delimitador+"""' CSV ;
			 """)

		except Exception as e:
			raise osv.except_osv("Alerta!","El Archivo ha importar posiblemente no es el correcto o contiene en alguno de sus campos como parte de su información el separador: '"+ self.delimitador + "'."+ "\n\n"+ str(e))

		self.env.cr.execute("""
			drop table if exists ventas_imp_productos_tmp_v2;

			create table ventas_imp_productos_tmp_v2 AS (
				select campo1,campo2,campo3,campo4,campo5,
				case when pc.id is not null then pc.id else """+str( self.env['product.category'].search([('codigo_categoria','=','SC')])[0].id )+""" end as campo6,
				pp.id as campo7
				 from ventas_imp_productos_tmp otm
				left join product_category pc on pc.codigo_categoria = otm.campo3
				left join product_product pp on pp.default_code = otm.campo1
			);
		 """)

		self.env.cr.execute("""
			copy (
			select distinct
				case when campo1 is null then 'No contiene codigo: ' || coalesce(campo2,'') else '-' end as codigo,
				case when campo2 is null then 'No contiene nombre: ' || coalesce(campo1,'') else '-' end as codigo
			from ventas_imp_productos_tmp_v2 where campo1 is null or campo2 is null
				)	
			TO '"""+ str( parametros.dir_create_file + 'iprv2.csv' )+ """'
			with delimiter '|'  CSV 

		 """)

		exp = open(str( parametros.dir_create_file + 'iprv2.csv' ),'r' ).read()

		self.file_sal_error_producto  = base64.encodestring(exp)


		if self.file_sal_error_producto:
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
		
		uom = str(self.env['product.uom'].search([('name','=','Unidad(es)')])[0].id)

		self.env.cr.execute(""" 
			INSERT INTO product_template (name,uom_id,uom_po_id,sale_ok,purchase_ok,type,categ_id,sale_line_warn,purchase_line_warn,active, tracking)
			select campo2,"""+uom+""","""+uom+""",true,true,'product',campo6,'no-message','no-message',true,'none'  from ventas_imp_productos_tmp_v2			
			where campo7 is null;			
		""")

		self.env.cr.execute(""" 
			INSERT INTO product_product(default_code,product_tmpl_id,active)
			select campo1,pt.id,true  from ventas_imp_productos_tmp_v2 optm
			inner join product_template pt on pt.name = optm.campo2
			where campo7 is null;	
		""")


		self.state = '3'




























class ventas_imp_clientes_tmp(models.Model):
	_name = 'ventas.imp.clientes.tmp'

	campo1 = fields.Char('col1')
	campo2 = fields.Char('col2')
	campo3 = fields.Char('col3')
	campo4 = fields.Char('col4')
	camporelleno = fields.Char('col5')



class importacion_partner_i(models.Model):
	_name='importacion.partner.i'

	state             = fields.Selection([('1','Borrador'),('2','Por Importar'),('3','Importado')],'Estado',readonly=True,default="1",copy=False)
	delimitador       = fields.Char('Delimitador', size=1, default=',')

	file_partner_imp = fields.Binary(u'Archivo importación productos', required=True)
	file_sal_error_partner = fields.Binary('Productos Paso 1 Errores', readonly=True,copy=False)

	period_id =fields.Many2one('account.period','Periodo',required=True)
	fecha = fields.Date('Fecha de Importacion')

	sal_name1 = fields.Char('Name 1',default='Observaciones_cliente_proveedor.csv')
	
	file_partner_imp_text = fields.Char(u'Archivo importación productos text')
	glosa = fields.Char('Glosa')
	_name_rec = 'fecha'


	@api.model
	def create(self, vals):
		if len( self.env['importacion.partner.i'].search([('state','in',('1','2'))]) ) >0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Por Importar.')

		#if len( self.env['importacion.partner.i'].search([('fecha','=',vals['fecha'])])):
		#	raise osv.except_osv("Alerta!", u"Ya existe una importación con la fecha "+vals['fecha'])
		t = super(importacion_partner_i, self).create(vals)
		return t

	@api.one
	def write(self,vals):
		if len( self.env['importacion.partner.i'].search([('state','in',('1','2')),('id','!=',self.id)]) )	>0:
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

		cabe_v1 = base64.b64decode(self.file_partner_imp)
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
		delete from ventas_imp_clientes_tmp;
		 """)

		try:
			self.env.cr.execute("""
			copy ventas_imp_clientes_tmp (campo1,campo2,campo3,campo4,camporelleno) from '""" +parametros.dir_create_file + 'iparv1.csv'+ """' with delimiter '"""+self.delimitador+"""' CSV ;
			 """)

		except Exception as e:
			raise osv.except_osv("Alerta!","El Archivo ha importar posiblemente no es el correcto o contiene en alguno de sus campos como parte de su información el separador: '"+ self.delimitador + "'." + "\n\n"+ str(e))

		self.env.cr.execute("""
			drop table if exists ventas_imp_clientes_tmp_v2;

			create table ventas_imp_clientes_tmp_v2 AS (
				select campo1,campo2,campo3,campo4, rp.id as campo5, itdp.id as campo6
				 from ventas_imp_clientes_tmp otm
				left join res_partner rp on rp.nro_documento = otm.campo1
				left join einvoice_catalog_06 itdp on itdp.code = (case when campo3 = 'DNI' then '1'  when campo3 = 'RUC' then '6' else campo3 end)
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
			INSERT INTO res_partner (is_company,name,display_name,type_document_partner_it,nro_documento,vat,lang,customer,supplier,active,notify_email,sale_warn,purchase_warn,picking_warn,invoice_warn)
			select true,campo2,campo2,campo6,campo1,campo1,'es_PE',true,true,true,true,'no-message','no-message','no-message','no-message'  from ventas_imp_clientes_tmp_v2 where campo5 is null;
		""")

		self.state = '3'


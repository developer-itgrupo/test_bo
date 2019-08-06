# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class import_codigo_sunat_util(models.Model):
	_name = 'import.codigo.sunat.util'

	cuenta_id = fields.Many2one('account.account','Cuenta')
	
	cuenta = fields.Char('Campo')
	codigo_sunat = fields.Char('Campo')


	wizard_id = fields.Many2one('wizard.import.codigo.sunat','Wizard')

class wizard_import_codigo_sunat(models.Model):
	_name = 'wizard.import.codigo.sunat'

	archivo = fields.Binary('CSV', help="El csv debe ir con la cabecera: cuenta, codigo_sunat")
	nombre = fields.Char('Nombre de Archivo')
	state = fields.Selection([('draft','Borrador'),('import','Importado')],'Estado',default='draft')
	
	detalle = fields.One2many('import.codigo.sunat.util','wizard_id','Detalle')
	delimitador = fields.Char('Delimitador',default=',')

	_rec_name = 'nombre'

	@api.model
	def create(self,vals):	
		if len( self.env['wizard.import.codigo.sunat'].search([('state','=',('draft'))]) ) >0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Cancelado.')
		t = super(wizard_import_codigo_sunat,self).create(vals)
		t.refresh()
		return t

	@api.one
	def write(self,vals):
		if len( self.env['wizard.import.codigo.sunat'].search([('state','=',('draft')),('id','!=',self.id)]) )	>0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Cancelado.')
		t = super(wizard_import_codigo_sunat,self).write(vals)
		self.refresh()
		return t

	@api.one
	def importar(self):
		import time		
		import base64
		import codecs
		self.delimitador= ','

		parametros = self.env['main.parameter'].search([])[0]

		cabe_v1 = base64.b64decode(self.archivo)
		file_cv1 = open(parametros.dir_create_file + 'codigo_sunat.csv','wb')
		file_cv1.write(cabe_v1)
		file_cv1.close()


		flag = False
		try:
			f = codecs.open(parametros.dir_create_file + 'codigo_sunat.csv',encoding='utf-8',errors='strict')
			f.read()
		except UnicodeDecodeError:
			flag= True

		if flag:
			import codecs
			BLOCKSIZE = 1048576 # or some other, desired size in bytes
			with codecs.open(parametros.dir_create_file + 'codigo_sunat.csv', "r", "iso-8859-1") as sourceFile:
				with codecs.open(parametros.dir_create_file + 'cod_s.csv', "w", "utf-8") as targetFile:
					while True:
						contents = sourceFile.read(BLOCKSIZE)
						if not contents:
							break
						targetFile.write(contents)
		else:			
			file_cv1 = open(parametros.dir_create_file + 'cod_s.csv','wb')
			file_cv1.write(cabe_v1)
			file_cv1.close()



		try:
			self.env.cr.execute("""	

			copy import_codigo_sunat_util (cuenta, codigo_sunat ) from '""" +parametros.dir_create_file + 'cod_s.csv'+ """' with delimiter '"""+self.delimitador+"""' CSV HEADER;
			 """)


			self.env.cr.execute("""
			update import_codigo_sunat_util set wizard_id = """ +str(self.id)+ """ where wizard_id is null ;
			 """)


		except Exception as e:
			raise osv.except_osv("Alerta!","El Archivo ha importar posiblemente no es el correcto o contiene en alguno de sus campos como parte de su información el separador: '"+ self.delimitador + "'."+ "\n\n"+ str(e))

		self.env.cr.execute("""
			
			update import_codigo_sunat_util set


			cuenta_id = T.v1

			from (
			
			select 
			iaa.id as id,
			aa.id as v1

			from import_codigo_sunat_util iaa
			left join account_account aa on aa.code = iaa.cuenta
			where iaa.wizard_id = """ +str(self.id)+ """ ) T where T.id = import_codigo_sunat_util.id
		 """)

		self.env.cr.execute("""
		select 
			cuenta_id,
			cuenta
			from import_codigo_sunat_util
			where wizard_id = """ +str(self.id)+ """
			and cuenta_id is null
			""")

		problemas = ""
		for i in self.env.cr.fetchall():
			problemas += "No se encontro la cuenta : " + i[1] + '\n'


		if problemas != "":
			raise osv.except_osv(problemas)

		self.env.cr.execute("""
			update 
				account_account set
					code_sunat = ics.codigo_sunat
					from import_codigo_sunat_util ics where ics.cuenta_id = account_account.id					
			""")
		
		self.state = 'import'


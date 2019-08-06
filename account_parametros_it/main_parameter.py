# -*- coding: utf-8 -*-

from odoo import http

from odoo import api, fields, models, _

class main_parameter(models.Model):
	_name = 'main.parameter'

	@api.model_cr
	def init(self):
		self.env.cr.execute('select id from res_users')
		uid = self.env.cr.dictfetchall()
		print 'uid', uid
		print 'uid0', uid[0]['id']
		self.env.cr.execute('select id from main_parameter')
		ids = self.env.cr.fetchall()
		
		print 'ids', ids
		
		if len(ids) == 0:
			self.env.cr.execute("""INSERT INTO main_parameter (create_uid, name) VALUES (""" + str(uid[0]['id']) + """, 'Parametros Generales');""")
	

	name = fields.Char('Nombre',size=50, default='Parametros Generales')
	deliver_account_mn = fields.Many2one('account.account','Rendicion Moneda Nacional')
	deliver_account_me = fields.Many2one('account.account','Rendicion Moneda Extranjera')
	loan_account_mn = fields.Many2one('account.account','Cuenta Prestamos')
	loan_account_me = fields.Many2one('account.account','Cuenta Prestamos M.E.')
	loan_journal_mn = fields.Many2one('account.journal','Diario Rendiciones M.N.')
	loan_journal_me = fields.Many2one('account.journal','Diario Rendiciones M.E.')
	export_document_id = fields.Many2one('einvoice.catalog.01', string="Documento de Exportacion",index=True,ondelete='restrict')
	no_home_document_id = fields.Many2one('einvoice.catalog.01', string="Comprobante de Pago No domiciliado",index=True,ondelete='restrict')
	no_home_debit_document_id = fields.Many2one('einvoice.catalog.01', string="N. Debito no domiciliado",index=True,ondelete='restrict')
	no_home_credit_document_id = fields.Many2one('einvoice.catalog.01', string="N. Credito no domiciliado",index=True,ondelete='restrict')
	
	sunat_type_document_ruc_id = fields.Many2one('einvoice.catalog.06', string="Tipo de Documento RUC",index=True,ondelete='restrict')
	l_ruc = fields.Integer(string="Longitud RUC")
	
	sunat_type_document_dni_id = fields.Many2one('einvoice.catalog.06', string="Tipo de Documento DNI",index=True,ondelete='restrict')
	l_dni = fields.Integer(string="Longitud DNI")
	
	sequence_gvinculado = fields.Many2one('ir.sequence', string='Secuencia para Gasto Vinculado')

	template_account_contable= fields.Many2one('account.chart.template','Código Plan de Cuentas')

	partner_null_id = fields.Many2one('res.partner','Partner para Anulaciones')
	product_null_id = fields.Many2one('product.product','Producto para Anulaciones')
	partner_venta_boleta  = fields.Many2one('res.partner','Partner para Ventas Boleta')

	dir_create_file = fields.Char('Directorio Exportadores', size=100)

	dir_ple_create_file = fields.Char('Directorio PLE', size=100)


	account_anticipo_proveedor_mn = fields.Many2one('account.account','Cuenta Anticipo Proveedor M.N.')
	account_anticipo_proveedor_me = fields.Many2one('account.account','Cuenta Anticipo Proveedor M.E.')
	account_anticipo_clientes_mn = fields.Many2one('account.account','Cuenta Anticipo Cliente M.N.')
	account_anticipo_clientes_me = fields.Many2one('account.account','Cuenta Anticipo Cliente M.E.')

	account_perception_igv = fields.Many2one('account.tax.code','Cuenta de Impuesto')
	account_perception_tipo_documento = fields.Many2one('einvoice.catalog.01','Tipo de Documento')

	diario_destino = fields.Many2one('account.journal','Diario Destino')

	fiscalyear = fields.Integer('Año Fiscal')

	account_cobranza_letras_mn = fields.Many2one('account.account','Cuenta Cobranza Letras M.N.')
	account_cobranza_letras_me = fields.Many2one('account.account','Cuenta Cobranza Letras M.E.')
	account_descuento_letras_mn = fields.Many2one('account.account','Cuenta Descuento Letras M.N.')
	account_descuento_letras_me = fields.Many2one('account.account','Cuenta Descuento Letras M.E.')
	download_directory = fields.Char('Directorio de Descarga/Completa')
	download_url = fields.Char('Directorio de Descarga/Url')


	@api.onchange('dir_ple_create_file')
	def onchange_dir_create_file(self):
		if self.dir_ple_create_file:
			if self.dir_ple_create_file[-1] == '/':
				pass
			else:
				self.dir_ple_create_file = self.dir_ple_create_file + '/'

	
	@api.onchange('dir_create_file')
	def onchange_dir_create_file(self):
		if self.dir_create_file:
			if self.dir_create_file[-1] == '/':
				pass
			else:
				self.dir_create_file = self.dir_create_file + '/'

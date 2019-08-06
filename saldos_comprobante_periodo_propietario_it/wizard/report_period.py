# -*- coding: utf-8 -*-

from openerp import models, fields, api

class saldo_comprobante_periodo_propietario(models.Model):

	_name='saldo.comprobante.periodo.propietario'
	_auto = False

	propietario = fields.Integer('Propietario')
	propietario_name = fields.Char('Propietario',compute="get_propietarioname")
	fecha_emi = fields.Date('Fecha Emisión')
	fecha_ven = fields.Date('Fecha Vencimiento')
	
	nro_documento = fields.Char('RUC')
	cliente = fields.Char('Empresa')
	tdoc = fields.Char('Tipo Cuenta')
	nro_comprobante = fields.Char('Cuenta')
	pventamn = fields.Float('Tipo Documento')
	pventame = fields.Float('Nro. Comprobante')
	cancelamn = fields.Float('Precio Venta Soles',digits=(12,2))
	cancelame = fields.Float('Precio Venta Dolares',digits=(12,2))
	saldomn = fields.Float('Cancelacion Soles',digits=(12,2))
	saldome = fields.Float('Cancelacion Dolares',digits=(12,2))
	moneda = fields.Char('Pendiente Soles',digits=(12,2))

	@api.one
	def get_propietarioname(self):
		if self.propietario:
			t = self.env['res.users'].browse(self.propietario)
			self.propietario_name = t.name
		else:
			self.propietario_name = ''
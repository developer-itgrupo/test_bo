# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _

class account_invoice(models.Model):
	_inherit='account.invoice'

	number = fields.Char(related=False,string="Nombre",store=True, readonly=True, copy=False)

	ckeck_modify_ple = fields.Boolean('Es Modificación')
	period_modify_ple = fields.Many2one('account.period','Periodo para PLE')
	ple_compra = fields.Selection([('0', 'ANOTACION OPTATIVAS SIN EFECTO EN EL IGV'), ('1', 'FECHA DEL DOCUMENTO CORRESPONDE AL PERIODO EN QUE SE ANOTO'), ('6', 'FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, DENTRO DE LOS 12 MESES'), ('7','FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, LUEGO DE LOS 12 MESES'),('9','ES AJUSTE O RECTIFICACION')], 'PLE Compras' ,default="1")
	ple_venta = fields.Selection([('0', 'ANOTACION OPTATIVA SIN EFECTO EN EL IGV'), ('1', 'FECHA DEL COMPROBANTE CORRESPONDE AL PERIODO'), ('2', 'DOCUMENTO ANULADO'), ('8', 'CORRESPONDE A UN PERIODO ANTERIOR'), ('9', 'SE ESTA CORRIGIENDO UNA ANOTACION DEL PERIODO ANTERIOR')], 'PLE Ventas' ,default="1")
	ple_diariomayor = fields.Selection([('1','FECHA DEL COMPROBANTE CORRESPONDE AL PERIODO'),('8', 'CORRESPONDE A UN PERIODO ANTERIOR Y NO HA SIDO ANOTADO EN DICHO PERIODO'), ('9', 'CORRESPONDE A UN PERIODO ANTERIOR Y SI HA SIDO ANOTADO EN DICHO PERIODO')], 'PLE Diario y Mayor' ,default="1")
	

	date_detraccion = fields.Date('Fecha',copy=False)
	voucher_number = fields.Char('Número de Comprobante',size=30,copy=False)
	code_operation= fields.Char('Codigo de Operación',size=50,copy=False)
	amount = fields.Float('Monto', digits=(12,2),copy=False)
	account_ids = fields.One2many('account.perception','father_invoice_id',string='Documentos Relacionados',copy=False)
	vacio = fields.Char('Vacio',size=30,copy=False)


	tipo_tasa_percepcion = fields.Char('Tipo Tasa',copy=False)
	numero_serie = fields.Char(u'Número de Documento',copy=False)



	tipo_sustento_credito_fiscasl = fields.Char('Tipo Documento',copy=False)
	serie_sustento_credito_fiscasl = fields.Char('Serie',copy=False)
	anio_sustento_credito_fiscasl = fields.Char('Año Emision Dua',copy=False)
	nro_comp_sustento_credito_fiscasl = fields.Char('Nro Comprobante',copy=False)




	# aqui van los de proveedor
	ultimo_numero_consolidado = fields.Char('Ultimo Número de Consolidado',size=100, copy=False)
	sujeto_a_retencion = fields.Boolean('Sujeto a Retención', copy=False)
	tipo_adquisicion = fields.Selection([('1','Mercaderia, materia prima, suministro, envases y embalajes'),('2','Activo Fijo'),('3','Otros activos no considerados en los numerales 1 y 2'),('4','Gastos de educación, recreación, salud, culturales, representación, capacitación, de viaje, mantenimiento de vehiculos, y de premios'),('5','Otros gastos no incluidos en el numeral 4')], 'Tipo Adquisición')
	contrato_o_proyecto = fields.Char('Contrato o Proyecto',size=200, copy=False)
	inconsistencia_tipo_cambio = fields.Boolean('Inconsistencia en Tipo de Cambio', copy=False)
	proveedor_no_habido = fields.Boolean('Proveedor No Habido', copy=False)
	renuncio_a_exoneracion_igv = fields.Boolean('Renuncio a Exoneracion IGV', copy=False)
	inconsistencia_dni_liquidacion_comp = fields.Boolean('Inconsistencia DNI en Liquidación Comp.', copy=False)
	cancelado_medio_pago = fields.Boolean('Cancelado con Medio de Pago', copy=False)
	estado_ple_compra = fields.Selection([('0', 'ANOTACION OPTATIVAS SIN EFECTO EN EL IGV'), ('1', 'FECHA DEL DOCUMENTO CORRESPONDE AL PERIODO EN QUE SE ANOTO'), ('6', 'FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, DENTRO DE LOS 12 MESES'), ('7','FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, LUEGO DE LOS 12 MESES'),('9','ES AJUSTE O RECTIFICACION')], 'PLE Compras' ,default="1",copy=False)
	periodo_ajuste_modificacion_ple = fields.Many2one('account.period','Periodo Ajuste PLE', copy=False)
	periodo_ajuste_modificacion_ple_compra = fields.Many2one('account.period','Periodo Ajuste PLE', copy=False)
	estado_ple = fields.Integer('Estado para PLE')


	#aqui van los de proveedor
	renta_bruta = fields.Float('Renta Bruta',digits=(12,2), copy=False)
	deduccion_costo_enajenacion = fields.Float('Deducción Costo Enajenacion',digits=(12,2), copy=False)
	renta_neta = fields.Float('Renta Neta',digits=(12,2), copy=False)
	tasa_de_retencion = fields.Float('Tasa de Retención',digits=(12,2), copy=False)
	impuesto_retenido = fields.Float('Impuesto Retenido',digits=(12,2), copy=False)
	exoneracion_aplicada = fields.Char('Exoneración Aplicada',size=200, copy=False)
	tipo_de_renta = fields.Char('Tipo de Renta',size=200, copy=False)
	modalidad_servicio_prestada = fields.Char('Modalidad Servicio Prestada',size=200, copy=False)
	aplica_art_del_impuesto = fields.Boolean('Aplicada Art 76 del Impuesto a la Renta', copy=False)
	beneficiario_de_pagos = fields.Many2one('res.partner','Beneficiario de los Pagos', copy=False)


	#aqui van los de cliente
	numero_final_consolidado_cliente = fields.Char('Ultimo Número de Consolidado',size=100, copy=False)
	numero_contrato_cliente = fields.Char('Número de contrato', size=200, copy=False)
	inconsistencia_tipo_cambio_cliente = fields.Boolean('Inconsistencia en Tipo de Cambio', copy=False)
	cancelado_medio_pago_cliente = fields.Boolean('Cancelado con Medio de Pago', copy=False)
	estado_ple_venta = fields.Selection([('0', 'ANOTACION OPTATIVA SIN EFECTO EN EL IGV'), ('1', 'FECHA DEL COMPROBANTE CORRESPONDE AL PERIODO'), ('2', 'DOCUMENTO ANULADO'), ('8', 'CORRESPONDE A UN PERIODO ANTERIOR'), ('9', 'SE ESTA CORRIGIENDO UNA ANOTACION DEL PERIODO ANTERIOR')], 'PLE Ventas' ,default='1',copy=False)
	periodo_ajuste_modificacion_ple_venta = fields.Many2one('account.period','Periodo Ajuste PLE', copy=False)


	it_type_document = fields.Many2one('einvoice.catalog.01','Tipo de Documento',required=False)

	currency_rate_auto = fields.Float('Tipo de Cambio Divisa',digits=(16,3))
	check_currency_rate = fields.Boolean('T.C. Personalizado?')


	serie_id = fields.Many2one('it.invoice.serie', string="Serie",index=True)
	serie_id_internal = fields.Many2one('it.invoice.serie', string="Serie",index=True,copy=False)
	nro_internal = fields.Char('Internal Number',copy=False)


	fecha_perception = fields.Date('Periodo Uso Percepcion')

	
	@api.multi
	def button_reset_taxes(self):
		self.compute_taxes()


class account_perception(models.Model):
	_name='account.perception'

	father_invoice_id = fields.Many2one('account.invoice',string="Factura")
	comprobante = fields.Char('Comprobante' ,size=50)
	tipo_doc = fields.Many2one('einvoice.catalog.01',string="T.D.",ondelete='restrict')
	fecha = fields.Date('Fecha Emisión')
	perception = fields.Float('Total', digits=(12,2))
	base_imponible = fields.Float('Base Imponible',digits=(12,2))
	igv = fields.Float('IGV',digits=(12,2))




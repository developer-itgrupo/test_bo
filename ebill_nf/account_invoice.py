# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint
import io
from xlsxwriter.workbook import Workbook
import sys
from datetime import datetime
from datetime import timedelta
import os
from dateutil.relativedelta import *
import decimal
import calendar
from openerp import models, fields, api
import urllib2
import json

class account_invoice(models.Model):
	_inherit='account.invoice'

	sunat_transaction_type = fields.Selection([
		('1',u'VENTA INTERNA'),
		('2',u'EXPORTACIÓN'),
		('3',u'NO DOMICILIADO'),
		('4',u'VENTA INTERNA – ANTICIPOS'),
		('5',u'VENTA ITINERANTE'),
		('6',u'FACTURA GUÍA'),
		('7',u'VENTA ARROZ PILADO'),
		('8',u'FACTURA - COMPROBANTE DE PERCEPCIÓN'),
		('10',u'FACTURA - GUÍA REMITENTE'),
		('11',u'FACTURA - GUÍA TRANSPORTISTA'),
		('12',u'BOLETA DE VENTA – COMPROBANTE DE PERCEPCIÓN'),
		('13',u'GASTO DEDUCIBLE PERSONA NATURAL'),
		], u'SUNAT Transacción',default="1")
	credit_invoice_type = fields.Many2one('einvoice.catalog.09',u'Tipo Nota Crédito')
	debit_invoice_type = fields.Many2one('einvoice.catalog.10',u'Tipo Nota Crédito')
	perception_type = fields.Selection([
		('1',u'PERCEPCIÓN VENTA INTERNA - TASA 2%'),
		('2',u'PERCEPCIÓN ADQUISICIÓN DE COMBUSTIBLE-TASA 1%'),
		('3',u'PERCEPCIÓN REALIZADA AL AGENTE DE PERCEPCIÓN CON TASA ESPECIAL - TASA 0.5%'),
		],u'Tipo de Percepción')
	preception_base = fields.Float(u'B. Imp. Percepción', digits=(12,2))
	perception_amount = fields.Float(u'Total Percepción', digits=(12,2))

	advance_payment_ids = fields.One2many('advance.payment','invoice_id','Anticipos')

	hash_ebill=fields.Char('Hash')
	url_pdf=fields.Char(u'Versión impresa')
	url_pdf2=fields.Char(u'Versión impresa web')
	cadena_qr=fields.Char(u'Cadena para codigo QR')


	have_detraction = fields.Boolean(u'Tiene detracción')
	detract = fields.Char(u'Tiene detracción')


	change_amount = fields.Float('Tipo de cambio')
	total_gravado=fields.Float('total_gravado')
	total_igv=fields.Float('total_igv')
	total_isc=fields.Float('total_isc')
	total_otros_cargos=fields.Float('total_otros_cargos')
	total_gratuita=fields.Float('total_gratuita')
	igv_porcentaje=fields.Float('igv_porcentaje')
	total_anticipos =fields.Float('total_anticipos')

	total_descuentos=fields.Float('total_descuentos')
	total_inafecto=fields.Float('total_inafecto')
	total_exonerado=fields.Float('total_exonerado')
	total_incluido_percepcion=fields.Float('total_incluido_percepción')

	sunat_ticket_anulacion = fields.Char('numero')


	@api.multi
	def cancel_eletronico_button(self):
		company = self[0].env.user.company_id
		parametros = self.env['main.parameter'].search([])[0]
		serie = self.env['serial.nubefact'].search([('serial_id','=',self[0].serie_id.id)])
		data_json={					
				"operacion": "generar_anulacion",
				"tipo_de_comprobante": self.it_type_document.code,
				"serie": self.reference.split('-')[0],
				"numero": self.reference.split('-')[1],
				"motivo": "ERROR DEL SISTEMA",
				"codigo_unico": "" 
		}
		jsonarray = json.dumps(data_json,indent=4)
		req = urllib2.Request(serie[0].path_nf)
		req.add_header('Content-Type', 'application/json')
		req.add_header('Authorization', 'Token token="'+serie[0].token_nf+'"')

		try:
			response = urllib2.urlopen(req, jsonarray)
		except urllib2.HTTPError as e:
			raise osv.except_osv('Error al procesar datos de factura electrónica', e.read())
		self.sunat_ticket_anulacion =respuesta ['sunat_ticket_numero']

	@api.multi
	def copy(self,default=None):
		default.update({'hash_ebill':False,'url_pdf':False,'url_pdf2':False})
		return super(account_invoice,self).copy(default)


	@api.multi
	def invoice_validate(self):
		if len(self)>1:
			raise osv.except_osv('Error!', u"Debido a la facturación electrónica no se puede procesar más de una factura a la vez")
		# if self.name == False:
		# 	raise osv.except_osv('Error!', u"Falta Ingresar referencia/descripción")

		res = super(account_invoice, self).invoice_validate()
		# raise osv.except_osv('Error!', self.move_id)
		parametros = self.env['main.parameter'].search([])[0]
		respuesta = self.make_einvoice()
		if(respuesta):
			self.hash_ebill = respuesta[0]
			self.url_pdf2= ( parametros.url_external_nf + ':' + respuesta[1].split(':')[2] ) if parametros.url_external_nf else ''
			self.url_pdf= respuesta[1]
			self.cadena_qr= respuesta[2]

		return res

	@api.multi
	def make_einvoice(self):
		company = self[0].env.user.company_id
		parametros = self.env['main.parameter'].search([])[0]
		serie = self.env['serial.nubefact'].search([('serial_id','=',self[0].serie_id.id)])
		if len(serie)==0:
			return
		if self[0].journal_id.type == 'sale' or self[0].journal_id.type == 'sale_refund':
		 	for self_act in self:
				if self_act.hash_ebill:
		 			return
		 		# esto se tiene que consultar el tipo de operacion sunat:
		 		# ventas ninternas, itinerantes, exportación y similares por ahora siempre 1 venta interna
		 		print 1
		 		sunat_transaction=self.sunat_transaction_type
		 		nombrecliente = ""
		 		if self_act.partner_id.is_company:
		 			nombrecliente=self_act.partner_id.name
		 		else:
		 			nombrecliente=str(self_act.partner_id.name)
		 			# nombrecliente=str(self_act.partner_id.first_name)
		 			# if self_act.partner_id.last_name_f:
		 			# 	nombrecliente=nombrecliente+" "+str(self_act.partner_id.last_name_f)
		 			# if self_act.partner_id.last_name_m:
		 			# 	nombrecliente=nombrecliente+" "+str(self_act.partner_id.last_name_m)
		 		documento_que_se_modifica_tipo=""
				documento_que_se_modifica_serie=""
				documento_que_se_modifica_numero=""
				tipo_de_nota_de_credito=""
				tipo_de_nota_de_debito=""
				if self_act.it_type_document.code=='07':
					tipo_de_nota_de_credito=str(int(self.credit_invoice_type.code))
				if self_act.it_type_document.code=='08':
					tipo_de_nota_de_debito=str(int(self.debit_invoice_type.code))
				if self_act.it_type_document.code=='07' or self_act.it_type_document.code=='08':
					if len(self_act.account_ids)==0:
						raise osv.except_osv('Error!', 'No se ha seleccionado un documento al que se afecta')
					docbase = self_act.account_ids[0]
					tdoc_1 = str(int(docbase.tipo_doc.code))
					if tdoc_1=='3':
						tdoc_1 = '2'
					if tdoc_1=='7':
						tdoc_1 ='3'
					if tdoc_1=='8':
						tdoc_1 = '4'
					documento_que_se_modifica_tipo=tdoc_1
					d= docbase.comprobante.split('-')
					documento_que_se_modifica_serie=d[0]
					documento_que_se_modifica_numero=d[1]
				tdoc = str(int(self_act.serie_id.type_document_id.code))
				if tdoc=='3':
					tdoc = '2'
				if tdoc=='7':
					tdoc ='3'
				if tdoc=='8':
					tdoc = '4'
				lineas          = []
				lineas_invoice  = []
				total_gravada   = 0
				total_inafecta  = 0
				total_exonerada = 0
				total_gratuita  = 0
				total_g         = self_act.amount_total
				ntotanticipo    = 0
				total_descuento = 0
				total_g         = 0
				othertax        = 0
				totalbaseimponible = 0
				total_igv =0
				total_igv_nograb=0
				deta = {}
				percent_igv=0
				ntotanticipo=0

				tax_percent=0
				total_igv_nf = 0

				# raise osv.except_osv('Error!', item)
				indice =0

				for linea in self_act.invoice_line_ids:
					
					tax_percent       = 0
					other_tax_percent = 0
					percent           = 0
					for impuesto in linea.invoice_line_tax_ids:
						if impuesto.amount_type == 'percent':
							percent=percent+impuesto.amount/100
						else:
							percent=percent+impuesto.amount
						if impuesto.tax_code_id.record_sale=='6':
							if impuesto.amount_type == 'percent':
								other_tax_percent=other_tax_percent+(impuesto.amount/100)
							else:
								other_tax_percent=other_tax_percent+impuesto.amount
						else:
							if impuesto.amount_type == 'percent':
				 				tax_percent =tax_percent+ impuesto.amount/100
				 			else:
				 				tax_percent =tax_percent+(impuesto.amount)
				 	if not impuesto.id:
				 		raise osv.except_osv('Error!', u'No puede crearse Lineas de Factura sin Impuestos')
					if impuesto.price_include:
						unit_included = linea.price_unit
						unit_noincluded = unit_included / (1 + percent)
					else:
						unit_included = linea.price_unit*(1+(impuesto.amount/100))
						unit_noincluded = linea.price_unit
					unit_noincluded=float(decimal.Decimal(str(unit_noincluded)).quantize(decimal.Decimal("1.1111"), decimal.ROUND_HALF_DOWN))
					descuento = abs(((unit_noincluded*(linea.discount/100))*linea.quantity))
					total_descuento = total_descuento + descuento
					totalsinimpuetos = linea.price_subtotal
					imp_igv=linea.price_subtotal*(percent-other_tax_percent)
					serie_a=""
					numero_a=""
					anticipo_regularizacion="false"
					if self_act.sunat_transaction_type=='4':
						if linea.product_id.id  == parametros.advance_product_id.id:
							if linea.price_subtotal<0:
								if len(self_act.advance_payment_ids)==0:
									raise osv.except_osv('Error!', u'La regularización del anticipo, debe tener el numero de documento indicado en la pestaña "Adelantos"')
								anticipo_regularizacion="true"
								ntotanticipo= ntotanticipo+abs(unit_noincluded*linea.quantity)
								nombre_p = parametros.advance_product_id.name
								serie_a = self_act.advance_payment_ids[0].serial
								numero_a = self_act.advance_payment_ids[0].number
					tipo_de_igv=False
					for impuesto in linea.invoice_line_tax_ids:
						if impuesto.tax_code_id.record_sale=='7':
							othertax=othertax+((unit_noincluded*linea.quantity)-descuento)*other_tax_percent
						if impuesto.ebill_tax_type:
							tipo_de_igv=impuesto.ebill_tax_type
						if impuesto.ebill_tax_type in ['1']:
							total_igv=total_igv+imp_igv
							total_gravada = total_gravada + float(decimal.Decimal(str(totalsinimpuetos)).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN))
						if impuesto.ebill_tax_type in ['8']:
							total_exonerada = total_exonerada + float(decimal.Decimal(str(totalsinimpuetos)).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN))
						if impuesto.ebill_tax_type in ['9','16']:
							total_inafecta = total_inafecta + abs(float(decimal.Decimal(str(totalsinimpuetos)).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))
						if impuesto.ebill_tax_type in ['6','2','3','4','5','7','10','11','12','13','14','15']:
							total_igv_nograb=total_igv_nograb+float(decimal.Decimal(str(abs(imp_igv))).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN))
							total_gratuita = total_gratuita + abs(float(decimal.Decimal(str(totalsinimpuetos+imp_igv)).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))

					umed = "NIU"
					if linea.product_id.type=='service':
						umed = 'ZZ'
					total_igv_nograb = float(decimal.Decimal(str(abs(total_igv_nograb))).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN))
					subtotal_r = float(decimal.Decimal(str(abs(totalsinimpuetos))).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN))
					igv_r      = float(decimal.Decimal(str(abs(imp_igv))).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN))
					total_r    = float(decimal.Decimal(str(abs(totalsinimpuetos+imp_igv))).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN))
					item={
							"unidad_de_medida": umed,
							"codigo": linea.product_id.default_code if linea.product_id.default_code else "",
							"descripcion": linea.name,
							"cantidad": linea.quantity,
							"valor_unitario": "%.6f" % abs(unit_noincluded)  if impuesto.ebill_tax_type not in ['6','2','3','4','5','7'] else "%.6f" % abs(unit_included),
							"precio_unitario": "%.6f" % abs(unit_included),
							"descuento": "%.2f" % descuento if descuento != 0 else "",
							"subtotal": "%.2f" % subtotal_r  if impuesto.ebill_tax_type not in ['6','2','3','4','5','7'] else "%.2f" % total_r,
							"tipo_de_igv": tipo_de_igv,
							"igv": "%.2f" % igv_r if impuesto.ebill_tax_type not in ['6','2','3','4','5','7'] else '0.00',
							"total": "%.2f" % total_r,
							"anticipo_regularizacion": anticipo_regularizacion,
							"anticipo_documento_serie": serie_a,
							"anticipo_documento_numero": numero_a
						 }

					lineas.append(item)
					item_upd={
						'porcentaje_impuesto':tax_percent,
						'precio_impuesto_incluido':float("%.6f" % abs(unit_included)),
						'precio_sin_impuestos_incluido':float ("%.6f" % abs(unit_noincluded)),
						'monto_descuento':float("%.2f" % descuento),
						'monto_igv':float("%.2f" % abs(igv_r)),
						'subtotal_impuesto':float("%.2f" % total_r),
						'subtotal_sin_impuesto':linea.price_subtotal,
						'invoice_line_id':linea.id,
						'tipo_de_igv':tipo_de_igv,
						"anticipo_regularizacion": anticipo_regularizacion,
						"anticipo_documento_serie": serie_a,
						"anticipo_documento_numero": numero_a
					}
					lineas_invoice.append(item_upd)
				DATETIME_FORMAT = "%Y-%m-%d"
				import pytz
				from openerp import SUPERUSER_ID
				totaligv_a=0
				totalother_a=0
				lineafinal=lineas[len(lineas)-1]
				lineafinal2=lineas_invoice[len(lineas_invoice)-1]
				for linea in lineas:
					if linea['anticipo_regularizacion']=='false':
						lineafinal=linea
						lineafinal2=linea
				montotaxof = 0

				total_igv=0


				total_gravada   =0
				total_exonerada =0
				total_inafecta  =0
				total_gratuita  =0
				for linea in lineas:
					if linea['anticipo_regularizacion']=='true':
						montobase=float(linea['subtotal'])*-1
					else:
						montobase=float(linea['subtotal'])

					if linea['tipo_de_igv'] in ['1']:
						total_gravada = total_gravada + montobase
					if linea['tipo_de_igv'] in ['8']:
						total_exonerada = total_exonerada + montobase
					if linea['tipo_de_igv'] in ['9','16']:
						total_inafecta = total_inafecta +montobase
					if linea['tipo_de_igv'] in ['6','2','3','4','5','7','10','11','12','13','14','15']:
						total_gratuita = total_gratuita + montobase

					if linea['anticipo_regularizacion']=='true':
						total_igv=total_igv-float(linea['igv'])
					else:
						total_igv=total_igv+float(linea['igv'])


				for taxline in self_act.tax_line_ids:
					montotaxof=montotaxof+taxline.amount
					if taxline.tax_id.tax_code_id.record_sale=='7':
						if total_igv+total_igv_nograb!=taxline.amount:
							dif=taxline.amount-total_igv+total_igv_nograb
							redo=abs(float(decimal.Decimal(str(dif)).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))
							vaclineaigvact = float(lineafinal['igv'])+round(round(dif,3),2)
							if total_igv_nograb==0:
								lineafinal.update({'igv':"%.2f" % vaclineaigvact})
								lineafinal2.update({'monto_igv':float("%.2f" % vaclineaigvact)})


				total_igv=0
				for linea in lineas:
					print float(linea['igv']),linea['igv']
					if linea['anticipo_regularizacion']=='true':
						total_igv=total_igv-float(linea['igv'])
					else:
						total_igv=total_igv+float(linea['igv'])

				if total_igv_nograb==0:
					othertax=float(decimal.Decimal(str(montotaxof-total_igv)).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN))
				else:
					othertax=0

				user_pool = self.pool.get('res.users')
				# pprint.pprint(self.env.uid)
				user = self.env['res.users'].browse(self.env.uid)
				tz = pytz.timezone(user.tz) or pytz.utc
				localized_datetime = pytz.utc.localize(datetime.strptime(self_act.date_invoice,DATETIME_FORMAT)).astimezone(tz)

				total_gravada_r      = abs(float(decimal.Decimal(str(total_gravada)).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))
				total_inafecta_r     = abs(float(decimal.Decimal(str(total_inafecta)).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))
				total_exonerada_r    = abs(float(decimal.Decimal(str(total_exonerada)).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))
				total_igv_r          = abs(float(decimal.Decimal(str((total_igv))).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))
				total_gratuita_r     = abs(float(decimal.Decimal(str(total_gratuita)).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))
				total_otros_cargos_r = abs(float(decimal.Decimal(str(othertax)).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))
				total_r              = abs(float(decimal.Decimal(str((total_gravada+othertax+total_exonerada+total_inafecta+total_igv))).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))


				observacion = (self_act.name or '')
				# cuentas = ", ".join(company.acc_number for company in self_act.company_id.bank_ids)
				# observacion += 2*'<br>' + cuentas
				observacion += 2*'<br>' + (self_act.comment or '')

				plazo_pago = ''
				if self_act.payment_term_id:
					plazo_pago = self_act.payment_term_id.name or ''
				# para las guias
				pikings= []
				guias_n = []
				ocompra = ""
				ocompras=[]
				for picking in pikings:
					guias_n.append({
						"guia_tipo":1,
						"guia_serie_numero":picking.numberg,
					})
					if picking.client_order_ref:
						if picking.client_order_ref not in ocompras:
							ocompra=ocompra+picking.client_order_ref+"/"
							ocompras.append(picking.client_order_ref)
				if len(ocompra)>20:
					ocompra=ocompra[:20]
				
				
				
				head_json = {
					"operacion": "generar_comprobante",
					"tipo_de_comprobante": tdoc,
					"serie": self_act.reference[0:4],
					"numero": int(self_act.reference[5:]),
					"sunat_transaction": sunat_transaction,
					"cliente_tipo_de_documento": str(int(self_act.partner_id.type_document_partner_it.code)),
					"cliente_numero_de_documento": self_act.partner_id.nro_documento,
					"cliente_denominacion": nombrecliente,
					"cliente_direccion": self_act.partner_id.street if self_act.partner_id.street else "",
					"cliente_email": self_act.partner_id.email if self_act.partner_id.email else "",
					"cliente_email_1": "",
					"cliente_email_2": "",
					"fecha_de_emision": self_act.date_invoice,
					"fecha_de_vencimiento": self_act.date_due,
					"moneda": 1 if self_act.currency_id.name == 'PEN' else 2,
					"tipo_de_cambio": "%.3f" % self_act.currency_rate_auto,
					"porcentaje_de_igv": "%.2f" % tax_percent,
					"descuento_global": "",
					"total_descuento": "%.6f" % total_descuento if total_descuento!=0 else "",
					"total_anticipo": "%.2f" % ntotanticipo,
					"total_gravada": "%.2f" % total_gravada_r,
					"total_inafecta": "%.2f" % total_inafecta_r,
					"total_exonerada": "%.2f" % total_exonerada_r,
					"total_igv": "%.2f" % total_igv_r,
					"total_gratuita": "%.2f" % total_gratuita_r,
					"total_otros_cargos": "%.2f" % total_otros_cargos_r,
					"total": "%.2f" % total_r,
					"percepcion_tipo": self.perception_type if self.perception_type else "",
					"percepcion_base_imponible": "%.2f" % self.preception_base if self.perception_type else "0.00",
					"total_percepcion": "%.2f" % self.perception_amount if self.perception_type else "0.00",
					"total_incluido_percepcion": "%.2f" % self_act.amount_total+self.perception_amount if self.perception_type else "0.00",
					"detraccion": "true" if self.have_detraction else "false",
					"observaciones": observacion,
					"documento_que_se_modifica_tipo": documento_que_se_modifica_tipo,
					"documento_que_se_modifica_serie": documento_que_se_modifica_serie,
					"documento_que_se_modifica_numero": documento_que_se_modifica_numero,
					"tipo_de_nota_de_credito": tipo_de_nota_de_credito,
					"tipo_de_nota_de_debito": tipo_de_nota_de_debito,
					"enviar_automaticamente_a_la_sunat": "false",
					"enviar_automaticamente_al_cliente": "true" if self_act.partner_id.email else 'false',
					"codigo_unico": "",
					"condiciones_de_pago": plazo_pago,
					"medio_de_pago": "",
					"placa_vehiculo": "",
					"orden_compra_servicio": ocompra,
					"tabla_personalizada_codigo": "",
					"formato_de_pdf": "",}

				head_json.update({'items':lineas})
				if len(guias_n)>0:
					head_json.update({'guias':guias_n})
				
				pprint.pprint(head_json)
				# raise osv.except_osv('Error!', head_json)
				vals = {
					'total_anticipos':float( "%.2f" % ntotanticipo),
					'total_descuentos':float("%.2f" % total_descuento),
					'total_gravado':float("%.2f" % total_gravada_r),
					'total_inafecto':float("%.2f" % total_inafecta_r),
					'total_exonerado':float("%.2f" % total_exonerada_r),
					'total_igv':float("%.2f" % total_igv_r),
					'total_gratuita':float("%.2f" % total_gratuita_r),
					'total_otros_cargos':float("%.2f" % total_otros_cargos_r),
					'total_incluido_percepcion':float("%.2f" % self_act.amount_total+self.perception_amount) if self.perception_type else 0.00,
				}
				self_act.write(vals)
				for linea_upd in lineas_invoice:
					vald=linea_upd['invoice_line_id']
					linea_invoice = self.env['account.invoice.line'].browse(vald)
					linea_invoice.write(linea_upd)



				# self.env['account.invoice.ebill'].create(vals)

				jsonarray = json.dumps(head_json,indent=4)
				req = urllib2.Request(serie[0].path_nf)
				req.add_header('Content-Type', 'application/json')
				req.add_header('Authorization', 'Token token="'+serie[0].token_nf+'"')

				try:
					response = urllib2.urlopen(req, jsonarray)
				except urllib2.HTTPError as e:
					raise osv.except_osv('Error al procesar datos de factura electrónica', e.read())
				respuesta = json.load(response)
				print str(respuesta)
				return (respuesta['codigo_hash'],respuesta['enlace_del_pdf'],respuesta['cadena_para_codigo_qr'])
		return False

class advance_payment(models.Model):
	_name='advance.payment'

	serial = fields.Char(u'Serie')
	number = fields.Char(u'Nro. Factrua')
	partner_id = fields.Many2one('res.partner','Cliente')
	name = fields.Char(u'Descripción',default="ANTICIPO")
	amount = fields.Float('Total',digits=(12,2))
	invoice_id = fields.Many2one('account.invoice',u'Factura de regularización')


class account_invoice_line(models.Model):
	_inherit='account.invoice.line'

	porcentaje_impuesto=fields.Float('porcentaje_impuesto')
	precio_impuesto_incluido=fields.Float('precio_impuesto_incluido')
	precio_sin_impuestos_incluido=fields.Float('precio_sin_impuestos_incluido')
	monto_descuento=fields.Float('monto_descuento')
	monto_igv=fields.Float('monto_igv')
	monto_otros_impuestos=fields.Float('monto_otros_impuestos')
	subtotal_impuesto=fields.Float('subtotal_impuesto')
	subtotal_sin_impuesto=fields.Float('subtotal_impuesto')
	tipo_de_igv=fields.Char('tipo_de_igv')
	anticipo_regularizacion=fields.Char('anticipo_regularizacion')
	anticipo_documento_serie=fields.Char('anticipo_documento_serie')
	anticipo_documento_numero=fields.Char('anticipo_documento_numero')




class product_template(models.Model):
	_inherit='product.template'

	code_onu = fields.Char('Codigo ONU',required=False)

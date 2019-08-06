# -*- encoding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv

class main_parameter(models.Model):
	_inherit = 'main.parameter'

	cuenta_cierre_contable = fields.Many2one('account.account','Cuenta Para Cierre contable')

class account_account(models.Model):
	_name='account.account'
	_inherit='account.account'		

	metodo_cierre = fields.Selection([('1','COSTO DE VENTAS'),('2',u'CANCELACION CLASE 9'),('3','MARGEN COMERCIAL'),('4','PRODUCCION DEL EJERCICIO'),('5','VALOR AGREGADO'),('6','EXCEDENTE O INSUFICIENCIA'),('7','RESULTADO DE EXPLOTACION'),('8','RESULTADO ANTES DE PARTICIPACIONES'),('9','CIERRE DE ACTIVO Y PASIVO')],'Metodo de Cierre')
	cuenta_cierre = fields.Many2one('account.account','Cuenta de Cierre')


class asiento_cierre_contable(models.Model):
	_name = 'asiento.cierre.contable'


	anio_fiscal = fields.Many2one('account.fiscalyear','Año Fiscal')
	period_cierre = fields.Many2one('account.period','Periodo de Cierre')
	journal_id = fields.Many2one('account.journal','Diario Cierre')

	state = fields.Selection([('draft','BORRADOR'),('0','GENERAR BALANCE COMPROBACION'),('1','COSTO DE VENTAS'),('2',u'CANCELACION CLASE 9'),('3','MARGEN COMERCIAL'),('4','PRODUCCION DEL EJERCICIO'),('5','VALOR AGREGADO'),('6','EXCEDENTE O INSUFICIENCIA'),('7','RESULTADO DE EXPLOTACION'),('8','RESULTADO ANTES DE PARTICIPACIONES'),('9','CIERRE DE ACTIVO Y PASIVO')],'Estado',default='draft')
	asiento_1 = fields.Many2one('account.move','Asiento Generado')
	asiento_2 = fields.Many2one('account.move','Asiento Generado')
	asiento_3 = fields.Many2one('account.move','Asiento Generado')
	asiento_4 = fields.Many2one('account.move','Asiento Generado')
	asiento_5 = fields.Many2one('account.move','Asiento Generado')
	asiento_6 = fields.Many2one('account.move','Asiento Generado')
	asiento_7 = fields.Many2one('account.move','Asiento Generado')
	asiento_8 = fields.Many2one('account.move','Asiento Generado')
	asiento_9 = fields.Many2one('account.move','Asiento Generado')

	dat1 = fields.Float('Margen Comercial')
	dat2 = fields.Float(u'Producción del Ejercicio')
	dat3 = fields.Float('Valor Agregado')
	dat4 = fields.Float('Excedente o Ins. Bruto de Explo.')
	dat5 = fields.Float(u'Resultado de explotación')
	dat6 = fields.Float('Resultado antes de par e impuestos')

	_rec_name = 'anio_fiscal'

	@api.one
	def cancelar(self):
		if self.state == '0':
			self.state = 'draft'

		if self.state == '1':
			self.state = '0'
			if self.asiento_1.id:
				if self.asiento_1.state != 'draft':
					self.asiento_1.button_cancel()
				self.env.cr.execute(""" delete from account_move_line where move_id = """+ str(self.asiento_1.id))
				self.asiento_1.unlink()

		elif self.state == '2':
			self.state = '1'
			if self.asiento_2.id:
				if self.asiento_2.state != 'draft':
					self.asiento_2.button_cancel()
				self.env.cr.execute(""" delete from account_move_line where move_id = """+ str(self.asiento_2.id))
				self.asiento_2.unlink()

		elif self.state == '3':
			self.state = '2'
			if self.asiento_3.id:
				if self.asiento_3.state != 'draft':
					self.asiento_3.button_cancel()
				self.env.cr.execute(""" delete from account_move_line where move_id = """+ str(self.asiento_3.id))
				self.asiento_3.unlink()

		elif self.state == '4':
			self.state = '3'
			if self.asiento_4.id:
				if self.asiento_4.state != 'draft':
					self.asiento_4.button_cancel()
				self.env.cr.execute(""" delete from account_move_line where move_id = """+ str(self.asiento_4.id))
				self.asiento_4.unlink()

		elif self.state == '5':
			self.state = '4'
			if self.asiento_5.id:
				if self.asiento_5.state != 'draft':
					self.asiento_5.button_cancel()
				self.env.cr.execute(""" delete from account_move_line where move_id = """+ str(self.asiento_5.id))
				self.asiento_5.unlink()

		elif self.state == '6':
			self.state = '5'
			if self.asiento_6.id:
				if self.asiento_6.state != 'draft':
					self.asiento_6.button_cancel()
				self.env.cr.execute(""" delete from account_move_line where move_id = """+ str(self.asiento_6.id))
				self.asiento_6.unlink()

		elif self.state == '7':
			self.state = '6'
			if self.asiento_7.id:
				if self.asiento_7.state != 'draft':
					self.asiento_7.button_cancel()
				self.env.cr.execute(""" delete from account_move_line where move_id = """+ str(self.asiento_7.id))
				self.asiento_7.unlink()

		elif self.state == '8':
			self.state = '7'
			if self.asiento_8.id:
				if self.asiento_8.state != 'draft':
					self.asiento_8.button_cancel()
				self.env.cr.execute(""" delete from account_move_line where move_id = """+ str(self.asiento_8.id))
				self.asiento_8.unlink()

		elif self.state == '9':
			self.state = '8'
			if self.asiento_9.id:
				if self.asiento_9.state != 'draft':
					self.asiento_9.button_cancel()
				self.env.cr.execute(""" delete from account_move_line where move_id = """+ str(self.asiento_9.id))
				self.asiento_9.unlink()

	@api.one
	def unlink(self):
		if self.state != 'draft':
			raise osv.except_osv('Alerta!', "No se puede eliminar un Cierre Contable que no este en borrador.")
		return super(asiento_cierre_contable,self).unlink()


	@api.one
	def cierre_contable_0(self):

		periodini = self.env['account.period'].search([('code','=','00/'+ self.anio_fiscal.name)])
		if len(periodini)>0:
			periodini = periodini[0]
		else:
			periodini = self.env['account.period'].search([('code','=','01/'+ self.anio_fiscal.name)])[0]


		periodfin = self.env['account.period'].search([('code','=','13/'+ self.anio_fiscal.name)])
		if len(periodfin)>0:
			periodfin = periodfin[0]
		else:
			periodfin = self.env['account.period'].search([('code','=','12/'+ self.anio_fiscal.name)])[0]


		hoja = self.env['account.sheet.work.detalle.wizard'].create({'type_show':'pantalla','period_ini':periodini.id,'period_end':periodfin.id,'wizrd_level_sheet':'2','fiscalyear_id':periodini.fiscalyear_id.id})
		hoja.do_rebuild()

		self.env.cr.execute(""" 
			DROP TABLE IF EXISTS account_sheet_work_detalle_guardado;
			CREATE  TABLE account_sheet_work_detalle_guardado as (
				select aa1.saldodeudor, aa1.saldoacredor, a2.id as cuenta_id, a2.cuenta_cierre, a2.metodo_cierre
				from account_sheet_work_detalle aa1 inner join account_account a2 on a2.code = aa1.cuenta ) ;
			""")
		self.state = '0'


	@api.one
	def cierre_contable_1(self):

		self.env.cr.execute(""" select saldodeudor, saldoacredor, cuenta_id, cuenta_cierre  
			from account_sheet_work_detalle_guardado where metodo_cierre = '1' """)
		tabla = self.env.cr.dictfetchall()

		asiento = self.env['account.move'].create({
				'journal_id':self.journal_id.id,
				#'period_id':self.period_cierre.id,
				'date':self.period_cierre.date_start,
			})

		self.asiento_1 = asiento.id

		for i in tabla:
			linea_i = {
					'name':'Asiento Cierre: Costo Ventas',
					'account_id':i['cuenta_id'],
					'debit':  0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor'],
					'credit': i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
					'move_id': asiento.id,
				}

			self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)

			linea_i = {
					'name':'Asiento Cierre: Costo Ventas',
					'account_id':i['cuenta_cierre'],
					'debit': i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0,
					'credit': 0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor'],
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
					'move_id': asiento.id,
				}
			self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)

		asiento.post()
		self.state = '1'




	@api.one
	def cierre_contable_2(self):
		self.env.cr.execute(""" select saldodeudor, saldoacredor, cuenta_id
			from account_sheet_work_detalle_guardado where metodo_cierre = '2' """)

		tabla = self.env.cr.dictfetchall()

		asiento = self.env['account.move'].create({
				'journal_id':self.journal_id.id,
				#'period_id':self.period_cierre.id,
				'date':self.period_cierre.date_start,
			})
		self.asiento_2 = asiento.id

		for i in tabla:
			linea_i ={
					'name':'Asiento Cierre: Cancelacion Clase 9',
					'account_id':i['cuenta_id'],
					'debit':  0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor'],
					'credit': i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
					'move_id': asiento.id,
				}
			self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)

		asiento.post()
		self.state = '2'


	@api.one
	def cierre_contable_3(self):
		param = self.env['main.parameter'].search([])[0]
		cuenta_cuadre = param.cuenta_cierre_contable.id

		if not cuenta_cuadre:
			raise osv.except_osv('Alerta!', "No se configuro la cuenta de cuadre para cierre contable.")

		self.env.cr.execute(""" select saldodeudor, saldoacredor, cuenta_id
			from account_sheet_work_detalle_guardado where metodo_cierre = '3' """)


		tabla = self.env.cr.dictfetchall()

		asiento = self.env['account.move'].create({
				'journal_id':self.journal_id.id,
				#'period_id':self.period_cierre.id,
				'date':self.period_cierre.date_start,
			})
		self.asiento_3 = asiento.id

		total = 0

		for i in tabla:
			linea_i = {
					'name':'Asiento Cierre: Margen Comercial',
					'account_id':i['cuenta_id'],
					'debit':  0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor'],
					'credit': i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
					'move_id': asiento.id,
				}
			self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)

			a1 = 0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor']
			a2 = i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0
			total += a1 - a2

		self.dat1 = total

		linea_i ={
				'name':'Asiento Cierre: Margen Comercial',
				'account_id':cuenta_cuadre,
				'debit':  0 if total > 0 else -total,
				'credit': total if total > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
				'move_id': asiento.id,
			}
		self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)

		asiento.post()
		self.state = '3'



	@api.one
	def cierre_contable_4(self):
		param = self.env['main.parameter'].search([])[0]
		cuenta_cuadre = param.cuenta_cierre_contable.id

		if not cuenta_cuadre:
			raise osv.except_osv('Alerta!', "No se configuro la cuenta de cuadre para cierre contable.")

		self.env.cr.execute(""" select saldodeudor, saldoacredor, cuenta_id
			from account_sheet_work_detalle_guardado where metodo_cierre = '4' """)

		tabla = self.env.cr.dictfetchall()

		asiento = self.env['account.move'].create({
				'journal_id':self.journal_id.id,
				#'period_id':self.period_cierre.id,
				'date':self.period_cierre.date_start,
			})
		self.asiento_4 = asiento.id

		total = 0

		for i in tabla:
			linea_i ={
					'name':'Asiento Cierre: Produccion del Ejercicio',
					'account_id':i['cuenta_id'],
					'debit':  0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor'],
					'credit': i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
					'move_id': asiento.id,
				}
			self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)
			a1 = 0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor']
			a2 = i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0
			total += a1 - a2

		self.dat2 = total

		linea_i ={
				'name':'Asiento Cierre: Produccion del Ejercicio',
				'account_id':cuenta_cuadre,
				'debit':  0 if total > 0 else -total,
				'credit': total if total > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
				'move_id': asiento.id,
			}
		self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)

		asiento.post()
		self.state = '4'


	@api.one
	def cierre_contable_5(self):
		param = self.env['main.parameter'].search([])[0]
		cuenta_cuadre = param.cuenta_cierre_contable.id

		if not cuenta_cuadre:
			raise osv.except_osv('Alerta!', "No se configuro la cuenta de cuadre para cierre contable.")

		self.env.cr.execute(""" select saldodeudor, saldoacredor, cuenta_id
			from account_sheet_work_detalle_guardado where metodo_cierre = '5' """)


		tabla = self.env.cr.dictfetchall()

		asiento = self.env['account.move'].create({
				'journal_id':self.journal_id.id,
				#'period_id':self.period_cierre.id,
				'date':self.period_cierre.date_start,
			})
		self.asiento_5 = asiento.id

		total = 0

		for i in tabla:
			linea_i ={
					'name':'Asiento Cierre: Valor Agregado',
					'account_id':i['cuenta_id'],
					'debit':  0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor'],
					'credit': i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
					'move_id': asiento.id,
				}
			self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)
			a1 = 0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor']
			a2 = i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0
			total += a1 - a2

		self.dat3 = self.dat1 + self.dat2 + total

		linea_i ={
				'name':'Asiento Cierre: Valor Agregado',
				'account_id':cuenta_cuadre,
				'debit':  0 if total > 0 else -total,
				'credit': total if total > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
				'move_id': asiento.id,
			}

		self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)
		asiento.post()
		self.state = '5'


	@api.one
	def cierre_contable_6(self):
		param = self.env['main.parameter'].search([])[0]
		cuenta_cuadre = param.cuenta_cierre_contable.id

		if not cuenta_cuadre:
			raise osv.except_osv('Alerta!', "No se configuro la cuenta de cuadre para cierre contable.")

		self.env.cr.execute(""" select saldodeudor, saldoacredor, cuenta_id
			from account_sheet_work_detalle_guardado where metodo_cierre = '6' """)


		tabla = self.env.cr.dictfetchall()

		asiento = self.env['account.move'].create({
				'journal_id':self.journal_id.id,
				#'period_id':self.period_cierre.id,
				'date':self.period_cierre.date_start,
			})
		self.asiento_6 = asiento.id

		total = 0

		for i in tabla:
			linea_i ={
					'name':'Asiento Cierre: Excedente o insuficiencia',
					'account_id':i['cuenta_id'],
					'debit':  0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor'],
					'credit': i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
					'move_id': asiento.id,
				}
			self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)
			a1 = 0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor']
			a2 = i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0
			total += a1 - a2

		self.dat4 = self.dat3 + total

		linea_i ={
				'name':'Asiento Cierre: Excedente o insuficiencia',
				'account_id':cuenta_cuadre,
				'debit':  0 if total > 0 else -total,
				'credit': total if total > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
				'move_id': asiento.id,
			}
		self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)

		asiento.post()
		self.state = '6'


	@api.one
	def cierre_contable_7(self):
		param = self.env['main.parameter'].search([])[0]
		cuenta_cuadre = param.cuenta_cierre_contable.id

		if not cuenta_cuadre:
			raise osv.except_osv('Alerta!', "No se configuro la cuenta de cuadre para cierre contable.")


		self.env.cr.execute(""" select saldodeudor, saldoacredor, cuenta_id
			from account_sheet_work_detalle_guardado where metodo_cierre = '7' """)


		tabla = self.env.cr.dictfetchall()

		asiento = self.env['account.move'].create({
				'journal_id':self.journal_id.id,
				#'period_id':self.period_cierre.id,
				'date':self.period_cierre.date_start,
			})
		self.asiento_7 = asiento.id

		total = 0

		for i in tabla:
			linea_i ={
					'name':'Asiento Cierre: Resultado de explotacion',
					'account_id':i['cuenta_id'],
					'debit':  0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor'],
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
					'credit': i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0,
					'move_id': asiento.id,
				}
			self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)
			a1 = 0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor']
			a2 = i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0
			total += a1 - a2

		self.dat5 = self.dat4 + total

		linea_i ={
				'name':'Asiento Cierre: Resultado de explotacion',
				'account_id':cuenta_cuadre,
				'debit':  0 if total > 0 else -total,
				'credit': total if total > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
				'move_id': asiento.id,
			}
		self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)

		asiento.post()
		self.state = '7'


	@api.one
	def cierre_contable_8(self):
		param = self.env['main.parameter'].search([])[0]
		cuenta_cuadre = param.cuenta_cierre_contable.id
		if not cuenta_cuadre:
			raise osv.except_osv('Alerta!', "No se configuro la cuenta de cuadre para cierre contable.")


		self.env.cr.execute(""" select saldodeudor, saldoacredor, cuenta_id
			from account_sheet_work_detalle_guardado where metodo_cierre = '8' """)


		tabla = self.env.cr.dictfetchall()

		asiento = self.env['account.move'].create({
				'journal_id':self.journal_id.id,
				#'period_id':self.period_cierre.id,
				'date':self.period_cierre.date_start,
			})
		self.asiento_8 = asiento.id

		total = 0

		for i in tabla:
			linea_i ={
					'name':'Asiento Cierre: Resultado antes de participaciones',
					'account_id':i['cuenta_id'],
					'debit':  0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor'],
					'credit': i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
					'move_id': asiento.id,
				}
			self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)
			a1 = 0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor']
			a2 = i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0
			total += a1 - a2


		self.dat6 = self.dat5 + total


		linea_i ={
				'name':'Asiento Cierre: Resultado antes de participaciones',
				'account_id':cuenta_cuadre,
				'debit':  0 if total > 0 else -total,
				'credit': total if total > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
				'move_id': asiento.id,
			}
		self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)

		asiento.post()
		self.state = '8'




	@api.one
	def cierre_contable_9(self):
		param = self.env['main.parameter'].search([])[0]
		cuenta_cuadre = param.cuenta_cierre_contable.id
		if not cuenta_cuadre:
			raise osv.except_osv('Alerta!', "No se configuro la cuenta de cuadre para cierre contable.")


		self.env.cr.execute(""" select saldodeudor, saldoacredor, cuenta_id
			from account_sheet_work_detalle_guardado where metodo_cierre = '9' """)

		tabla = self.env.cr.dictfetchall()

		asiento = self.env['account.move'].create({
				'journal_id':self.journal_id.id,
				#'period_id':self.period_cierre.id,
				'date':self.period_cierre.date_start,
			})
		self.asiento_9 = asiento.id

		total = 0

		for i in tabla:
			linea_i ={
					'name':'Asiento Cierre: Cierre de activo y pasivo',
					'account_id':i['cuenta_id'],
					'debit':  0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor'],
					'credit': i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
					'move_id': asiento.id,
				}
			self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)
			a1 = 0 if i['saldodeudor']-i['saldoacredor'] > 0 else i['saldoacredor']-i['saldodeudor']
			a2 = i['saldodeudor']-i['saldoacredor'] if i['saldodeudor']-i['saldoacredor'] > 0 else 0
			total += a1 - a2


		linea_i ={
				'name':'Asiento Cierre: Cierre de activo y pasivo',
				'account_id':cuenta_cuadre,
				'debit':  0 if total > 0 else -total,
				'credit': total if total > 0 else 0,
					#'period_id':asiento.period_id.id,
					'journal_id':asiento.journal_id.id,
				'move_id': asiento.id,
			}
		self.env.cr.execute("""
				insert into account_move_line(create_uid, name,account_id,debit,credit,journal_id,move_id,company_id,date) ValUeS ("""+ STR(self.env.uid)+ """,'""" + linea_i['name'] + """',""" + str(linea_i['account_id']) + """,""" + str(linea_i['debit']) + """,""" + str(linea_i['credit']) + """,""" +  str(linea_i['journal_id']) + """,""" + str(asiento.id) + """,1,'"""+str(asiento.date)+"""');
			 """)

		asiento.post()
		self.state = '9'

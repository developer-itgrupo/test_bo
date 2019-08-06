# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class account_transfer_it(models.Model):
	_name = 'account.transfer.it'

	name = fields.Char('Nombre',default='/')

	fecha = fields.Date('Fecha')
	doc_origen = fields.Char('Doc. Origen',size=12)
	doc_destino = fields.Char('Doc. Destino',size=12)
	glosa = fields.Char('Glosa')

	caja_origen = fields.Many2one('account.journal','Caja Origen')
	monto = fields.Float('Monto Origen')
	tc_oficial = fields.Float('T.C. Oficial',digits=(12,3), compute="get_tc_oficial")

	caja_destino = fields.Many2one('account.journal','Caja Destino')
	nro_destino = fields.Many2one('account.bank.statement','Nro. Destino')
	monto_destino = fields.Float('Monto Destino')
	tc_personalizado = fields.Float('T.C. Personalizado',digits=(12,3))

	asiento_origen = fields.Many2one('account.move','Asiento Origen')
	asiento_destino = fields.Many2one('account.move','Asiento Destino')
	state = fields.Selection([('draft','Borrador'),('transfer','Transferido'),('cancel','Cancelado')],'Estado',default='draft')

	@api.model
	def create(self,vals):
		t = super(account_transfer_it,self).create(vals)
		t.onchange_monto()
		return t
	

	@api.one
	def write(self,vals):
		t = super(account_transfer_it,self).write(vals)
		if 'hola' in vals:
			pass
		else:
			self.refresh()
			

			cambio = self.tc_oficial
			if self.tc_personalizado:
				cambio = self.tc_personalizado
			total = 0
			if not self.caja_origen or not self.caja_destino:
				total=0

			else:
				if self.caja_origen.currency_id.id == self.caja_destino.currency_id.id:
					total = self.monto
				elif self.caja_origen.currency_id.id:
					total = self.monto * cambio
				else:
					total = self.monto / cambio if cambio != 0 else 0
			self.write({'monto_destino':total,'hola':1})
		return t
	

	@api.onchange('monto','caja_origen','caja_destino','fecha','tc_personalizado')
	def onchange_monto(self):
		cambio = self.tc_oficial
		if self.tc_personalizado:
			cambio = self.tc_personalizado

		if not self.caja_origen or not self.caja_destino:
			self.monto_destino=0

		else:
			if self.caja_origen.currency_id.id == self.caja_destino.currency_id.id:
				self.monto_destino = self.monto
			elif self.caja_origen.currency_id.id:
				self.monto_destino = self.monto * cambio
			else:
				self.monto_destino = self.monto / cambio if cambio != 0 else 0

	@api.onchange('fecha')
	def onchange_fecha(self):
		tmp = 0

		if self.fecha:
			self.env.cr.execute(""" select type_sale from res_currency_rate rcr 
				inner join res_currency rc on rc.id = rcr.currency_id
				where rcr.name = '""" +self.fecha+ """' and rc.name = 'USD'
			  """)
			for i in self.env.cr.fetchall():
				tmp = i[0]

		self.tc_oficial = tmp

	@api.one
	def reestablecername(self):
		self.name = '/'

	@api.one
	def get_tc_oficial(self):
		tmp = 0

		if self.fecha:
			self.env.cr.execute(""" select type_sale from res_currency_rate rcr 
				inner join res_currency rc on rc.id = rcr.currency_id
				where rcr.name = '""" +self.fecha+ """' and rc.name = 'USD'
			  """)
			for i in self.env.cr.fetchall():
				tmp = i[0]

		self.tc_oficial = tmp

	@api.one
	def transferir(self):
		id_seq = self.env['ir.sequence'].search([('name','=','Seq. Transferencias')])
		if len(id_seq)>0:
			id_seq = id_seq[0]
		else:
			id_seq = self.env['ir.sequence'].create({'name':'Seq. Transferencias','implementation':'standard','active':True,'prefix':'TRANSF-','padding':4,'number_increment':1,'number_next_actual' :1})
		if self.name == '/':
			self.write({'name': id_seq.next_by_id()})

		param_conf = self.env['res.company'].search([])[0]
		if not self.caja_origen.default_debit_account_id.id or not self.caja_destino.default_debit_account_id.id or not param_conf.transfer_account_id.id:
			raise ValidationError( 'No configuro la cuenta de transferencia o la de debito por defecto en el Diario')

		tc_usar = self.tc_oficial
		if self.tc_personalizado:
			tc_usar = self.tc_personalizado

		linea1 = (0,0,{
			'name':self.glosa,
			'nro_comprobante': self.doc_origen,
			'account_id': param_conf.transfer_account_id.id,
			'debit': self.monto*tc_usar if self.caja_origen.currency_id.id else self.monto,
			'credit':0,
			#'move_id':obj_a1.id,
		})

		linea2 = (0,0,{
			'name':self.glosa,
			'nro_comprobante': self.doc_origen,
			'account_id': self.caja_origen.default_debit_account_id.id,
			'debit': 0,
			'credit':self.monto*tc_usar if self.caja_origen.currency_id.id else self.monto,
			#'move_id':obj_a1.id,
		})

		if self.caja_origen.currency_id.id:
			linea2[2]['currency_id']= self.caja_origen.currency_id.id
			linea2[2]['amount_currency']= -self.monto
			linea2[2]['tc']= tc_usar
		

		asiento1 = {
			'date':self.fecha,
			'journal_id':self.caja_origen.id,
			'ref':self.doc_origen,
			'line_ids':[linea1,linea2],
		}
		obj_a1 = self.env['account.move'].create(asiento1)





		linea2 = (0,0,{
			'name':self.glosa,
			'nro_comprobante': self.doc_destino,
			'account_id': self.caja_destino.default_debit_account_id.id,
			'debit': self.monto_destino*tc_usar if self.caja_destino.currency_id.id else self.monto_destino,
			'credit':0,
			#'move_id':obj_a2.id,
			'statement_id': self.nro_destino.id,
		})

		if self.caja_destino.currency_id.id:
			linea2[2]['currency_id']= self.caja_destino.currency_id.id
			linea2[2]['amount_currency']= self.monto_destino
			linea2[2]['tc']= tc_usar
		

		linea1 = (0,0,{
			'name':self.glosa,
			'nro_comprobante': self.doc_destino,
			'account_id': param_conf.transfer_account_id.id,
			'debit': 0,
			'credit':self.monto_destino*tc_usar if self.caja_destino.currency_id.id else self.monto_destino,
			#'move_id':obj_a2.id,
		})


		asiento2 = {
			'date':self.fecha,
			'journal_id':self.caja_destino.id,
			'ref':self.doc_destino,
			'line_ids':[linea2,linea1],
		}
		obj_a2 = self.env['account.move'].create(asiento2)



		self.asiento_origen = obj_a1.id
		if obj_a1.state == 'draft':
			obj_a1.post()
		self.asiento_destino = obj_a2.id
		if obj_a2.state == 'draft':
			obj_a2.post()

		self.state = 'transfer'

	@api.one
	def cancel(self):
		if self.asiento_origen.id:
			if self.asiento_origen.state!= 'draft':
				self.asiento_origen.button_cancel()
			self.asiento_origen.unlink()

		if self.asiento_destino.id:
			if self.asiento_destino.state!= 'draft':
				self.asiento_destino.button_cancel()
			self.asiento_destino.unlink()

		self.state = 'cancel'

	@api.one
	def borrador(self):
		self.state = 'draft'


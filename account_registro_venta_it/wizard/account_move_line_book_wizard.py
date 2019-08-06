# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

class export_file_save(osv.TransientModel):
	_name = 'export.file.save'	
	
	output_name = fields.Char('Output filename', size=128)
	output_file = fields.Binary('Output file', readonly=True, filename="output_name")

class account_move_line_book_wizard(osv.TransientModel):
	_name='account.move.line.book.wizard'
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	asientos =  fields.Selection([('posted','Asentados'),('draft','No Asentados'),('both','Ambos')], 'Asientos')
	moneda = fields.Many2one('res.currency','Moneda')
	type_show =  fields.Selection([('pantalla','Pantalla'),('csv','Csv'),('pdf','Pdf')], 'Mostrar en', required=True)
	libros = fields.Many2many('account.journal','account_book_journal_rel','id_book_origen','id_journal_destino', string='Libros', required=True)




	@api.onchange('period_ini')
	def _change_periodo_ini(self):
		if self.period_ini:
			self.period_end= self.period_ini


	@api.multi
	def do_rebuild(self):
		fechaini_obj = self.period_ini
		fechafin_obj = self.period_end
		filtro = []
		
		t = self.env['account.period'].search([('id','>=',fechaini_obj.id),('id','<=',fechafin_obj.id)]).mapped('name')
		filtro.append( ('periodo','in',tuple(t)) )

		if self.asientos:
			if self.asientos == 'posted':
				filtro.append( ('statefiltro','=','posted') )
			if self.asientos == 'draft':
				filtro.append( ('statefiltro','=','draft') )
		if self.moneda:
			company_obj = self.env['res.company'].search([]).mapped('currency_id')
			if self.moneda in company_obj:
				print "todo bien"
			else:
				raise osv.except_osv('Alerta','Ese tipo de Moneda aún esta en desarrollo (Por favor comunicarse con ITGrupo).')

		if self.libros:
			libros_list = []
			for i in  self.libros:
				libros_list.append(i.code)
			filtro.append( ('libro','in',tuple(libros_list)) )
		
		move_obj=self.env['account.move.line.book']

		lstidsmove = move_obj.search(filtro)



		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
		
		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			
			result = mod_obj.get_object_reference('account_contable_book_it', 'action_account_moves_all_it')
			
			id = result and result[1] or False
			print id
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.move.line.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'res_id': id,
				'views': [(False, 'tree')],
			}
		if self.type_show == 'pdf':
			raise osv.except_osv('Alerta','Aún esta en desarrollo (Por favor comunicarse con ITGrupo).')
		if self.type_show == 'csv':
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			Str_csv = lstidsmove.mapped(lambda r: self.csv_convert(r,'|'))
			rpta = ""
			for i in Str_csv:
				rpta += i.encode('iso-8859-1') + "\n"

			vals = {
				'output_name': 'LibroDiario.csv',
				'output_file': base64.encodestring(rpta),		
			}
			sfs_id = self.env['export.file.save'].create(vals)
			result = {}
			view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read( [view_id] )
			print sfs_id
			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}



	@api.multi
	def csv_verif_integer(self,data):
		if data:
			return str(data)
		else:
			return ''

	@api.multi
	def csv_verif(self,data):
		if data:
			return data
		else:
			return ''
	@api.multi
	def csv_convert(self,data,separador):
		tmp = self.csv_verif(data.periodo)
		tmp += separador+ self.csv_verif(data.libro)
		tmp += separador+ self.csv_verif(data.voucher)
		tmp += separador+ self.csv_verif(data.cuenta)
		tmp += separador+ self.csv_verif_integer(data.debe)
		tmp += separador+ self.csv_verif_integer(data.haber)
		tmp += separador+ self.csv_verif(data.divisa)
		tmp += separador+ self.csv_verif_integer(data.tipodecambio)
		tmp += separador+ self.csv_verif_integer(data.importedivisa)
		tmp += separador+ self.csv_verif(data.codigo)
		tmp += separador+ self.csv_verif(data.partner)
		tmp += separador+ self.csv_verif(data.tipodocumento)
		tmp += separador+ self.csv_verif(data.numero)
		tmp += separador+ self.csv_verif(data.fechaemision)
		tmp += separador+ self.csv_verif(data.fechavencimiento)
		tmp += separador+ self.csv_verif(data.glosa)
		tmp += separador+ self.csv_verif(data.ctaanalitica) 
		tmp += separador+ self.csv_verif(data.refconcil )
		return unicode(tmp)



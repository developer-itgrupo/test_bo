# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class import_asiento_apertura(models.Model):
	_name = 'import.asiento.apertura'

	ruc = fields.Char('RUC')
	razon_social = fields.Many2one('res.partner','Razon Social')
	fecha_emision = fields.Date('Fecha Emision')
	fecha_vencimiento = fields.Date('Fecha Vencimiento')
	vendedor = fields.Many2one('res.users','Vendedor')
	tipo_doc = fields.Many2one('einvoice.catalog.01','Tipo Doc.')
	numero = fields.Char('Numero')
	moneda = fields.Many2one('res.currency','Moneda')
	saldo_mn = fields.Float('Saldo MN')
	saldo_me = fields.Float('Saldo ME')
	cuenta = fields.Many2one('account.account','Cuenta')
	tipo_cambio = fields.Float('Tipo Cambio')

	campo1 = fields.Char('Campo')
	campo2 = fields.Char('Campo')
	campo3 = fields.Char('Campo')
	campo4 = fields.Char('Campo')
	campo5 = fields.Char('Campo')
	campo6 = fields.Char('Campo')
	campo7 = fields.Char('Campo')
	campo8 = fields.Char('Campo')
	campo9 = fields.Char('Campo')
	campo10 = fields.Char('Campo')
	campo11 = fields.Char('Campo')
	campo12 = fields.Char('Campo')

	n_ruc = fields.Char('Campo')
	n_razonsoc = fields.Char('Campo')
	n_fecha_emision = fields.Char('Campo')
	n_fecha_vencimiento = fields.Char('Campo')
	n_vendedor = fields.Char('Campo')
	n_tipo_doc = fields.Char('Campo')
	n_numero = fields.Char('Campo')
	n_moneda = fields.Char('Campo')
	n_saldo_mn = fields.Char('Campo')
	n_saldo_me = fields.Char('Campo')
	n_cuenta = fields.Char('Campo')
	n_tipo_cambio = fields.Char('Campo')

	wizard_id = fields.Many2one('wizard.import.asiento.apertura','Wizard')

class wizard_import_asiento_apertura(models.Model):
	_name = 'wizard.import.asiento.apertura'

	fecha_contable = fields.Date('Fecha Contable')
	cuenta_descargo_mn = fields.Many2one('account.account','Cuenta de Descargo Soles')
	cuenta_descargo_me = fields.Many2one('account.account','Cuenta de Descargo Dolares')
	partner_descargo = fields.Many2one('res.partner','Partner Descargo')
	documento_descargo = fields.Char('Documento Descargo')
	archivo = fields.Binary('CSV', help="El csv debe ir con la cabecera: n_ruc, n_razonsoc, n_fecha_emision, n_fecha_vencimiento, n_vendedor, n_tipo_doc, n_numero, n_moneda, n_saldo_mn, n_saldo_me, n_cuenta, n_tipo_cambio")
	nombre = fields.Char('Nombre de Archivo')
	state = fields.Selection([('draft','Borrador'),('import','Importado'),('cancel','Cancelado')],'Estado',default='draft')
	diario = fields.Many2one('account.journal','Diario')

	detalle = fields.One2many('import.asiento.apertura','wizard_id','Detalle')
	tipo = fields.Selection([('1','Cliente'),('2','Proveedor')],'Tipo')
	delimitador = fields.Char('Delimitador',default=',')


	_rec_name = 'nombre'

	@api.model
	def create(self,vals):	
		if len( self.env['wizard.import.asiento.apertura'].search([('state','in',('draft','cancel'))]) ) >0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Cancelado.')
		t = super(wizard_import_asiento_apertura,self).create(vals)
		t.refresh()
		return t

	@api.one
	def write(self,vals):
		if len( self.env['wizard.import.asiento.apertura'].search([('state','in',('draft','cancel')),('id','!=',self.id)]) )	>0:
			raise osv.except_osv('Alerta!','Existe otra importacion pendiente en estado Borrador o Cancelado.')
		t = super(wizard_import_asiento_apertura,self).write(vals)
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
		file_cv1 = open(parametros.dir_create_file + 'asientoinicial.csv','wb')
		file_cv1.write(cabe_v1)
		file_cv1.close()


		flag = False
		try:
			f = codecs.open(parametros.dir_create_file + 'asientoinicial.csv',encoding='utf-8',errors='strict')
			f.read()
		except UnicodeDecodeError:
			flag= True

		if flag:
			import codecs
			BLOCKSIZE = 1048576 # or some other, desired size in bytes
			with codecs.open(parametros.dir_create_file + 'asientoinicial.csv', "r", "iso-8859-1") as sourceFile:
				with codecs.open(parametros.dir_create_file + 'asientoini.csv', "w", "utf-8") as targetFile:
					while True:
						contents = sourceFile.read(BLOCKSIZE)
						if not contents:
							break
						targetFile.write(contents)
		else:			
			file_cv1 = open(parametros.dir_create_file + 'asientoini.csv','wb')
			file_cv1.write(cabe_v1)
			file_cv1.close()



		try:
			self.env.cr.execute("""	

			copy import_asiento_apertura (n_ruc, n_razonsoc, n_fecha_emision, n_fecha_vencimiento, n_vendedor, n_tipo_doc, n_numero, n_moneda, n_saldo_mn, n_saldo_me, n_cuenta, n_tipo_cambio) from '""" +parametros.dir_create_file + 'asientoini.csv'+ """' with delimiter '"""+self.delimitador+"""' CSV HEADER;
			 """)


			self.env.cr.execute("""
			update import_asiento_apertura set wizard_id = """ +str(self.id)+ """ where wizard_id is null ;
			 """)


			self.env.cr.execute("""	

			update import_asiento_apertura set 
				campo1 = n_ruc, 
				campo2 = n_razonsoc, 
				campo3 = n_fecha_emision, 
				campo4 = n_fecha_vencimiento,
				campo5 = n_vendedor, 
				campo6 = n_tipo_doc, 
				campo7 = n_numero, 
				campo8 = n_moneda, 
				campo9 = n_saldo_mn, 
				campo10 = n_saldo_me,
				campo11 = n_cuenta, 
				campo12 = n_tipo_cambio where wizard_id = """ +str(self.id)+ """;
			 """)

		except Exception as e:
			raise osv.except_osv("Alerta!","El Archivo ha importar posiblemente no es el correcto o contiene en alguno de sus campos como parte de su información el separador: '"+ self.delimitador + "'."+ "\n\n"+ str(e))



		self.env.cr.execute("""
			select distinct
				coalesce(campo1,'') as ver_partner,
				coalesce(campo2,'') as ver_partner
			from import_asiento_apertura iaa 
			left join res_partner rp on rp.nro_documento = iaa.campo1
			where rp.id is null
		 """)

		for ptas in self.env.cr.fetchall():
			tta = {
					'name': ptas[1],
					'nro_documento': ptas[0]
			}
			self.env['res.partner'].create(tta)




		self.env.cr.execute("""
			
			update import_asiento_apertura set


			ruc = T.v1,
			razon_social = T.v2,
			fecha_emision = T.v3::date,
			fecha_vencimiento = T.v4::date,
			vendedor = T.v5,
			tipo_doc = T.v6,
			numero = T.v7,
			moneda = T.v8,
			saldo_mn = T.v9::numeric,
			saldo_me = T.v10::numeric,
			cuenta = T.v11,
			tipo_cambio = T.v12::numeric

			from (
			select 
			iaa.id as id,
			iaa.campo1 as v1,
			rp.id as v2,
			iaa.campo3 as v3,
			iaa.campo4 as v4,
			ru.id as v5,
			ec.id as v6,
			iaa.campo7 as v7,
			rc.id as v8,
			iaa.campo9 as v9,
			iaa.campo10 as v10,
			aa.id as v11,
			iaa.campo12 as v12

			from import_asiento_apertura iaa
			left join res_partner rp on rp.nro_documento = iaa.campo1
			left join res_partner rpp2 on rpp2.name = iaa.campo5
			left join res_users ru on ru.partner_id = rpp2.id
			left join einvoice_catalog_01 ec on ec.code = iaa.campo6
			left join res_currency rc on rc.name = iaa.campo8
			left join account_account aa on aa.code = iaa.campo11
			where iaa.wizard_id = """ +str(self.id)+ """ ) T where T.id = import_asiento_apertura.id
		 """)

		self.env.cr.execute("""
		select ruc,
			razon_social,
			vendedor,
			campo5,
			cuenta,
			campo11
			from import_asiento_apertura
			where wizard_id = """ +str(self.id)+ """
			""")

		problemas = ""
		for i in self.env.cr.fetchall():
			#if not i[2]:
			#	problemas += "No se encontro el vendedor : " + i[3] + '\n'
			if not i[4]:
				problemas += "No se encontro la cuenta : " + i[5] + '\n'

		if problemas != "":
			raise osv.except_osv(problemas)



		self.env.cr.execute("""

			INSERT INTO account_move(fecha_contable,date,name,state,journal_id,ref,company_id,ple_diariomayor, apertura_id,fecha_special) 
			select '"""+str(self.fecha_contable)+"""',fecha_emision, campo1 ||'-' || tipo_doc ||'-' || numero , 'posted',"""+str(self.diario.id)+""", numero,1, '1',"""+str(self.id)+""","""+('true' if ( str(self.fecha_contable) == '-01-01') else 'false' )+""" from import_asiento_apertura
			where wizard_id = """ +str(self.id)+ """;		
		
			""")
		#if self.tipo =='1':
		if True:
			self.env.cr.execute(""" 
				INSERT INTO account_move_line(name,partner_id,nro_comprobante,
				account_id,date_maturity,
				debit,credit,
				amount_currency,currency_id,tax_code_id,
				tax_amount,tc,type_document_it,journal_id,date, move_id,company_id) 

				select 'SALDOS INICIALES', """+str(self.partner_descargo.id)+""" , '""" +str(self.documento_descargo)+ """',
				CASE 
					WHEN rc.name = 'USD' then """ +str(self.cuenta_descargo_me.id)+ """
					else """ +str(self.cuenta_descargo_mn.id)+ """
				end,iaa.fecha_vencimiento,
				CASE WHEN iaa.saldo_mn >0 then 0 else 
						CASE 
							WHEN rc.name = 'USD' then abs(iaa.saldo_mn)
							else abs(iaa.saldo_mn)
						end 
				end,
				CASE WHEN iaa.saldo_mn >0 then 
						CASE 
							WHEN rc.name = 'USD' then abs(iaa.saldo_mn)
							else abs(iaa.saldo_mn)
						end  else 0
				end,
				CASE 
					WHEN rc.name = 'USD' then -iaa.saldo_me
					else 0
				end,CASE 
					WHEN rc.name = 'USD' then iaa.moneda
					else null
				end,null,
				0,iaa.tipo_cambio,(select id from einvoice_catalog_01 where code = '00'), am.journal_id, am.date, am.id, 1
				from import_asiento_apertura iaa
				inner join account_move am on am.name = campo1 ||'-' || iaa.tipo_doc || '-' || iaa.numero and am.apertura_id = """ +str(self.id)+ """
				left join res_currency rc on rc.id = iaa.moneda
				where iaa.wizard_id = """ +str(self.id)+ """

				union all

				select '/', iaa.razon_social , iaa.numero,
				iaa.cuenta ,iaa.fecha_vencimiento,
				CASE WHEN iaa.saldo_mn >0 then 
						CASE 
							WHEN rc.name = 'USD' then abs(iaa.saldo_mn)
							else abs(iaa.saldo_mn)
						end  else 0
				end,

				CASE WHEN iaa.saldo_mn >0 then 0 else 
						CASE 
							WHEN rc.name = 'USD' then abs(iaa.saldo_mn)
							else abs(iaa.saldo_mn)
						end 
				end,

				CASE 
					WHEN rc.name = 'USD' then iaa.saldo_me
					else 0
				end,CASE 
					WHEN rc.name = 'USD' then iaa.moneda
					else null
				end,null::integer,
				0,iaa.tipo_cambio,iaa.tipo_doc, am.journal_id, am.date, am.id, 1
				from import_asiento_apertura iaa
				inner join account_move am on am.name = campo1 ||'-' || iaa.tipo_doc || '-' || iaa.numero and am.apertura_id = """ +str(self.id)+ """
				left join res_currency rc on rc.id = iaa.moneda
				where iaa.wizard_id = """ +str(self.id)+ """

				;		
			""")

			self.env.cr.execute("""

				update account_move_line set
					amount_residual = abs(debit - credit),
					amount_residual_currency = amount_currency
				where move_id in (select id from account_move where apertura_id = """ +str(self.id)+ """ );
				--and account_id in (select aa.id from account_account aa inner join account_account_type aat on aat.id = aa.user_type_id where aat.type in ('payable','receivable') )
				UPDATE ACCOUNT_MOVE_LINE SET amount_residual = debit-credit ,  amount_residual_currency = amount_currency , CREDIT_CASH_BASIS = CREDIT, DEBIT_CASH_BASIS = DEBIT, RECONCILED= false, BALANCE_CASH_BASIS = DEBIT-CREDIT where move_id in (select am.id from account_move am where am.apertura_id = """ +str(self.id)+ """);
				
				""")
		else:
			self.env.cr.execute(""" 
				INSERT INTO account_move_line(name,partner_id,nro_comprobante,
				account_id,date_maturity,
				debit,credit,
				amount_currency,currency_id,tax_code_id,
				tax_amount,tc,type_document_it,journal_id,date, move_id,company_id) 

				select 'SALDOS INICIALES', """+str(self.partner_descargo.id)+""" , '""" +str(self.documento_descargo)+ """',
				CASE 
					WHEN rc.name = 'USD' then """ +str(self.cuenta_descargo_me.id)+ """
					else """ +str(self.cuenta_descargo_mn.id)+ """
				end,iaa.fecha_vencimiento,
				CASE WHEN iaa.saldo_me >0 then 
						CASE 
							WHEN rc.name = 'USD' then iaa.saldo_mn
							else iaa.saldo_mn
						end  else 0
				end,

				CASE WHEN iaa.saldo_me >0 then 0 else 
						CASE 
							WHEN rc.name = 'USD' then -iaa.saldo_mn
							else -iaa.saldo_mn
						end 
				end,CASE 
					WHEN rc.name = 'USD' then iaa.saldo_me
					else 0
				end,CASE 
					WHEN rc.name = 'USD' then iaa.moneda
					else null
				end,null,
				0,iaa.tipo_cambio,(select id from einvoice_catalog_01 where code = '00'), am.journal_id, am.date, am.id, 1
				from import_asiento_apertura iaa
				inner join account_move am on am.name = campo1 ||'-' || iaa.tipo_doc || '-' || iaa.numero and am.apertura_id = """ +str(self.id)+ """
				left join res_currency rc on rc.id = iaa.moneda
				where iaa.wizard_id = """ +str(self.id)+ """

				union all

				select '/', iaa.razon_social , iaa.numero,
				iaa.cuenta ,iaa.fecha_vencimiento,
				CASE WHEN iaa.saldo_me >0 then 0 else 
						CASE 
							WHEN rc.name = 'USD' then -iaa.saldo_mn
							else -iaa.saldo_mn
						end 
				end,
				CASE WHEN iaa.saldo_me >0 then 
						CASE 
							WHEN rc.name = 'USD' then iaa.saldo_mn
							else iaa.saldo_mn
						end  else 0
				end,CASE 
					WHEN rc.name = 'USD' then -iaa.saldo_me
					else 0
				end,CASE 
					WHEN rc.name = 'USD' then iaa.moneda
					else null
				end,null::integer,
				0,iaa.tipo_cambio,iaa.tipo_doc, am.journal_id, am.date, am.id, 1
				from import_asiento_apertura iaa
				inner join account_move am on am.name = campo1 ||'-' || iaa.tipo_doc || '-' || iaa.numero and am.apertura_id = """ +str(self.id)+ """
				left join res_currency rc on rc.id = iaa.moneda
				where iaa.wizard_id = """ +str(self.id)+ """

				;		
			""")

			self.env.cr.execute("""

				update account_move_line set
					amount_residual = abs(debit - credit),
					amount_residual_currency = amount_currency
				where move_id in (select id from account_move where apertura_id = """ +str(self.id)+ """ );
				--and account_id in (select aa.id from account_account aa inner join account_account_type aat on aat.id = aa.user_type_id where aat.type in ('payable','receivable') )

				UPDATE ACCOUNT_MOVE_LINE SET amount_residual = debit-credit ,  amount_residual_currency = amount_currency , CREDIT_CASH_BASIS = CREDIT, DEBIT_CASH_BASIS = DEBIT, RECONCILED= false, BALANCE_CASH_BASIS = DEBIT-CREDIT where move_id in (select am.id from account_move am where am.apertura_id = """ +str(self.id)+ """);
				""")


		if self.tipo =='1':
			self.env.cr.execute("""
				INSERT INTO account_invoice(number,partner_id,it_type_document,reference,
				currency_id,date_invoice,journal_id,
				amount_total_signed,residual_signed,amount_untaxed, amount_total,residual,	move_id,company_id,account_id,
				reference_type,type,state,apertura_id,currency_rate_auto,user_id,sunat_transaction_type,check_currency_rate)
				
				select iaa.numero, iaa.razon_social, iaa.tipo_doc, iaa.numero,
				iaa.moneda, iaa.fecha_emision, am.journal_id,
				CASE 
					WHEN rc.name = 'USD' then iaa.saldo_me 
					else iaa.saldo_mn
				end,CASE 
					WHEN rc.name = 'USD' then iaa.saldo_me 
					else iaa.saldo_mn
				end,CASE 
					WHEN rc.name = 'USD' then iaa.saldo_me 
					else iaa.saldo_mn
				end,CASE 
					WHEN rc.name = 'USD' then iaa.saldo_me 
					else iaa.saldo_mn
				end,CASE 
					WHEN rc.name = 'USD' then iaa.saldo_me 
					else iaa.saldo_mn
				end, am.id, 1, iaa.cuenta,
				'none',
				CASE WHEN ecc.code in ('07','08') THEN '""" +('out_refund' if self.tipo == '1' else 'in_refund' )+ """'
				else '""" +('out_invoice' if self.tipo == '1' else 'in_invoice' )+ """' end,'open',

				 """+str(self.id)+ """, iaa.tipo_cambio , iaa.vendedor ,'1',true

				from import_asiento_apertura iaa
				inner join account_move am on am.name = campo1 ||'-' || iaa.tipo_doc || '-' || iaa.numero and am.apertura_id = """ +str(self.id)+ """
				left join res_currency rc on rc.id = iaa.moneda
				left join einvoice_catalog_01 ecc on ecc.id = iaa.tipo_doc
				where iaa.wizard_id = """ +str(self.id)+"""
				;
				""")


			self.env.cr.execute("""
				INSERT INTO account_invoice_line(name,account_id,quantity, price_unit, price_subtotal, invoice_id)
				
				select 'SALDOS INICIALES', CASE 
					WHEN rc.name = 'USD' then """ +str(self.cuenta_descargo_me.id)+ """
					else """ +str(self.cuenta_descargo_mn.id)+ """
				end,1, CASE 
					WHEN rc.name = 'USD' then iaa.saldo_me
					else iaa.saldo_mn
				end, CASE 
					WHEN rc.name = 'USD' then iaa.saldo_me
					else iaa.saldo_mn
				end, ai.id
				from import_asiento_apertura iaa
				inner join account_move am on am.name = campo1 ||'-' || iaa.tipo_doc || '-' || iaa.numero and am.apertura_id = """ +str(self.id)+ """
				inner join account_invoice ai on ai.move_id = am.id
				left join res_currency rc on rc.id = iaa.moneda
				where iaa.wizard_id = """ +str(self.id)+"""
				;
				""")
		else:
			self.env.cr.execute("""
				INSERT INTO account_invoice(number,partner_id,it_type_document,reference,
				currency_id,date_invoice,journal_id,
				amount_total_signed,residual_signed,amount_untaxed, amount_total,residual,	move_id,company_id,account_id,
				reference_type,type,state,apertura_id,currency_rate_auto,user_id,sunat_transaction_type,check_currency_rate)
				
				select iaa.numero, iaa.razon_social, iaa.tipo_doc, iaa.numero,
				iaa.moneda, iaa.fecha_emision, am.journal_id,
				CASE 
					WHEN rc.name = 'USD' then -iaa.saldo_me 
					else -iaa.saldo_mn
				end,CASE 
					WHEN rc.name = 'USD' then -iaa.saldo_me 
					else -iaa.saldo_mn
				end,CASE 
					WHEN rc.name = 'USD' then -iaa.saldo_me 
					else -iaa.saldo_mn
				end,CASE 
					WHEN rc.name = 'USD' then -iaa.saldo_me 
					else -iaa.saldo_mn
				end,CASE 
					WHEN rc.name = 'USD' then -iaa.saldo_me 
					else -iaa.saldo_mn
				end, am.id, 1, iaa.cuenta,
				'none',
				CASE WHEN ecc.code in ('07','08') THEN '""" +('out_refund' if self.tipo == '1' else 'in_refund' )+ """'
				else '""" +('out_invoice' if self.tipo == '1' else 'in_invoice' )+ """' end,'open',

				 """+str(self.id)+ """, iaa.tipo_cambio , iaa.vendedor ,'1',true

				from import_asiento_apertura iaa
				inner join account_move am on am.name = campo1 ||'-' || iaa.tipo_doc || '-' || iaa.numero and am.apertura_id = """ +str(self.id)+ """
				left join res_currency rc on rc.id = iaa.moneda
				left join einvoice_catalog_01 ecc on ecc.id = iaa.tipo_doc
				where iaa.wizard_id = """ +str(self.id)+"""
				;
				""")


			self.env.cr.execute("""
				INSERT INTO account_invoice_line(name,account_id,quantity, price_unit, price_subtotal, invoice_id)
				
				select 'SALDOS INICIALES', CASE 
					WHEN rc.name = 'USD' then """ +str(self.cuenta_descargo_me.id)+ """
					else """ +str(self.cuenta_descargo_mn.id)+ """
				end,1, CASE 
					WHEN rc.name = 'USD' then -iaa.saldo_me
					else -iaa.saldo_mn
				end, CASE 
					WHEN rc.name = 'USD' then -iaa.saldo_me
					else -iaa.saldo_mn
				end, ai.id
				from import_asiento_apertura iaa
				inner join account_move am on am.name = campo1 ||'-' || iaa.tipo_doc || '-' || iaa.numero and am.apertura_id = """ +str(self.id)+ """
				inner join account_invoice ai on ai.move_id = am.id
				left join res_currency rc on rc.id = iaa.moneda
				where iaa.wizard_id = """ +str(self.id)+"""
				;
				""")



		self.state = 'import'


	@api.one
	def eliminar(self):
		
		self.env.cr.execute(""" 
			ALTER TABLE account_move_line DISABLE TRIGGER all;
			delete from account_move_line where move_id in (select move_id from account_invoice where apertura_id = """+str(self.id)+""");
			ALTER TABLE account_move_line ENABLE TRIGGER all;

			""")

		self.env.cr.execute(""" 
			ALTER TABLE account_move DISABLE TRIGGER all;
			delete from account_move where id in (select move_id from account_invoice where apertura_id = """+str(self.id)+""");
			ALTER TABLE account_move ENABLE TRIGGER all;
			""")

		self.env.cr.execute(""" 
			ALTER TABLE account_invoice_line DISABLE TRIGGER all;
			delete from account_invoice_line where invoice_id in (select id from account_invoice where apertura_id = """+str(self.id)+""");
			ALTER TABLE account_invoice_line ENABLE TRIGGER all;
			""")

		self.env.cr.execute(""" 
			ALTER TABLE account_invoice DISABLE TRIGGER all;
			delete from account_invoice where id in (select id from account_invoice where apertura_id = """+str(self.id)+""");
			ALTER TABLE account_invoice ENABLE TRIGGER all;
			""")
		
		self.env.cr.execute(""" 
			ALTER TABLE import_asiento_apertura DISABLE TRIGGER all;
			delete from import_asiento_apertura where wizard_id = """+str(self.id)+""";
			ALTER TABLE import_asiento_apertura ENABLE TRIGGER all;
			""")


		self.state = 'cancel'

	@api.one
	def borrador(self):
		self.state = 'draft'

	@api.one
	def unlink(self):
		if self.state != 'draft':
			raise osv.except_osv('No se puede eliminar una importacion en proceso.')
		for i in self.detalle:
			i.unlink()
		t = super(wizard_import_asiento_apertura,self).unlink()
		return t


class account_invoice(models.Model):
	_inherit = 'account.invoice'

	apertura_id = fields.Many2one('wizard.import.asiento.apertura','Apertura ID')




class account_move(models.Model):
	_inherit = 'account.move'

	apertura_id = fields.Many2one('wizard.import.asiento.apertura','Apertura ID')



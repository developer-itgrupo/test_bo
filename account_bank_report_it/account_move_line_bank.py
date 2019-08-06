# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv

def number_to_letter(number):
	UNIDADES = (
		'',
		'UN ',
		'DOS ',
		'TRES ',
		'CUATRO ',
		'CINCO ',
		'SEIS ',
		'SIETE ',
		'OCHO ',
		'NUEVE ',
		'DIEZ ',
		'ONCE ',
		'DOCE ',
		'TRECE ',
		'CATORCE ',
		'QUINCE ',
		'DIECISEIS ',
		'DIECISIETE ',
		'DIECIOCHO ',
		'DIECINUEVE ',
		'VEINTE '
	)

	DECENAS = (
		'VENTI',
		'TREINTA ',
		'CUARENTA ',
		'CINCUENTA ',
		'SESENTA ',
		'SETENTA ',
		'OCHENTA ',
		'NOVENTA ',
		'CIEN '
	)

	CENTENAS = (
		'CIENTO ',
		'DOSCIENTOS ',
		'TRESCIENTOS ',
		'CUATROCIENTOS ',
		'QUINIENTOS ',
		'SEISCIENTOS ',
		'SETECIENTOS ',
		'OCHOCIENTOS ',
		'NOVECIENTOS '
	)

	MONEDAS = (
		{'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
		{'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
		{'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
		{'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
		{'country': u'Perú', 'currency': 'PEN', 'singular': u'SOL', 'plural': u'SOLES', 'symbol': u'S/.'},
		{'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
	)
	# Para definir la moneda me estoy basando en los código que establece el ISO 4217
	# Decidí poner las variables en inglés, porque es más sencillo de ubicarlas sin importar el país
	# Si, ya sé que Europa no es un país, pero no se me ocurrió un nombre mejor para la clave.

	def __convert_group(n):
		"""Turn each group of numbers into letters"""
		output = ''

		if(n == '100'):
			output = "CIEN"
		elif(n[0] != '0'):
			output = CENTENAS[int(n[0]) - 1]

		k = int(n[1:])
		if(k <= 20):
			output += UNIDADES[k]
		else:
			if((k > 30) & (n[2] != '0')):
				output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
			else:
				output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
		return output
	#raise osv.except_osv('Alerta', number)
	number=str(round(float(number),2))
	separate = number.split(".")
	number = int(separate[0])

	if int(separate[1]) >= 0:
		moneda = "con " + str(separate[1]).ljust(2,'0') + "/" + "100 " 

	"""Converts a number into string representation"""
	converted = ''
	
	if not (0 <= number < 999999999):
		raise osv.except_osv('Alerta', number)
		#return 'No es posible convertir el numero a letras'

	
	
	number_str = str(number).zfill(9)
	millones = number_str[:3]
	miles = number_str[3:6]
	cientos = number_str[6:]
	

	if(millones):
		if(millones == '001'):
			converted += 'UN MILLON '
		elif(int(millones) > 0):
			converted += '%sMILLONES ' % __convert_group(millones)

	if(miles):
		if(miles == '001'):
			converted += 'MIL '
		elif(int(miles) > 0):
			converted += '%sMIL ' % __convert_group(miles)

	if(cientos):
		if(cientos == '001'):
			converted += 'UN '
		elif(int(cientos) > 0):
			converted += '%s ' % __convert_group(cientos)
	if float(number_str)==0:
		converted += 'CERO '
	converted += moneda

	return converted.upper()



class account_bank_report(models.Model):
	_name = 'account.bank.report'
	_auto = False


	@api.multi
	def compute_saldo_me(self):
		SaldoN = 0
		for x in self.sorted(key=lambda r: r.id):
			SaldoN += x.cargo_me
			SaldoN -= x.abono_me
			x.saldo_me = SaldoN


	@api.multi
	def compute_saldo_mn(self):
		SaldoN = 0
		for x in self.sorted(key=lambda r: r.id):
			SaldoN += x.cargo_mn
			SaldoN -= x.abono_mn
			x.saldo_mn = SaldoN


	@api.one
	def compute_documento(self):
		array_payments = []
		for pagos in self.nro_asiento.line_ids:
			if pagos.payment_id.id:
				array_payments.append(pagos.payment_id)

		if len(array_payments) == 0:
			self.documento = False
		elif len(array_payments) >1:
			self.documento = 'Varios'
		else:
			self.documento = array_payments[0].nro_comprobante
		return True

	fecha = fields.Date('Fecha')
	cheque = fields.Char('Cheque',size=200)
	nombre = fields.Char('Nombre / Razón Social',size=200)
	documento = fields.Char('Documento',compute="compute_documento")
	glosa = fields.Char('Glosa',size=200)
	cargo_mn = fields.Float('Cargo M.N.',digits=(12,2))
	abono_mn = fields.Float('Abono M.N.',digits=(12,2))
	saldo_mn = fields.Float('Saldo M.N.',digits=(12,2), compute="compute_saldo_mn")
	tipo_cambio = fields.Float('T/C',digits=(12,3))
	cargo_me = fields.Float('Cargo M.E.',digits=(12,2))
	abono_me = fields.Float('Abono M.E.',digits=(12,2))
	saldo_me = fields.Float('Saldo M.E.',digits=(12,2), compute="compute_saldo_me")
	
	nro_asiento = fields.Many2one('account.move','Nro. de Asiento')
	aa_id = fields.Integer('aa_id')

	diario_id = fields.Integer('Diario')

class libro_auxiliar_caja_banco(models.Model):
	_name='libro.auxiliar.caja.banco'

	_auto = False

	@api.model_cr
	def init(self):
		self.env.cr.execute("""
			DROP FUNCTION IF EXISTS get_report_bank_with_saldoinicial(boolean, integer, integer) cascade;
CREATE OR REPLACE FUNCTION get_report_bank_with_saldoinicial(IN has_currency boolean, IN periodo_ini integer, IN periodo_fin integer)
	RETURNS TABLE(id bigint, fecha date, cheque varchar, nombre varchar,documento varchar, glosa varchar, cargo_mn numeric, abono_mn numeric, tipo_cambio numeric, cargo_me numeric, abono_me numeric, nro_asiento integer,aa_id integer ,ordenamiento integer, diario_id integer) AS
$BODY$
BEGIN

IF $3 is Null THEN
		$3 := $2;
END IF;

RETURN QUERY 
SELECT row_number() OVER () AS id,*
	 FROM ( SELECT * from(
	 	SELECT 
	 	aml.date AS fecha,
	 	aml.nro_comprobante AS cheque,
	 	rp.name as nombre,

	 	am.name as documento,
	 	
	 	aml.name as glosa,
	 	aml.debit as cargo_mn,
	 	aml.credit as abono_mn,
	 	aml.tc as tipo_cambio,
	 	CASE WHEN aml.amount_currency>0 THEN aml.amount_currency ELSE 0 END as cargo_me,
	 	CASE WHEN aml.amount_currency<0 THEN -1*aml.amount_currency ELSE 0 END as abono_me,
	 	am.id as nro_asiento,
	 	aa.id as aa_id,
	 	1 as ordenamiento,
	 	aj.id as diario_id


		FROM account_move_line aml
		 JOIN account_journal aj ON aj.id = aml.journal_id
		 JOIN account_move am ON am.id = aml.move_id
		 JOIN account_period ap ON ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable  and ap.special = am.fecha_special
		 JOIN account_account aa ON aa.id = aml.account_id
		 LEFT JOIN einvoice_means_payment mp ON mp.id = am.means_payment_it
		 LEFT JOIN res_currency rc ON rc.id = aml.currency_id
		 LEFT JOIN res_partner rp ON rp.id = aml.partner_id
		 LEFT JOIN einvoice_catalog_01 itd ON itd.id = aml.type_document_it
		 LEFT JOIN account_analytic_account aaa ON aaa.id = aml.analytic_account_id
	WHERE periodo_num(ap.name) >= $2 and periodo_num(ap.name) <= $3
	and am.state != 'draft'
	
UNION ALL

SELECT 
	 	Null::date AS fecha,
	 	Null::varchar AS cheque,
	 	Null::varchar AS nombre,
	 	Null::varchar as documento,
	 	'Saldo Inicial' as glosa,
	 	sum(aml.debit) as cargo_mn,		
		sum(aml.credit) as abono_mn,
	 	Null::numeric as tipo_cambio,
	 	
	 	sum( CASE WHEN aml.amount_currency>0 THEN aml.amount_currency else 0 END ) as cargo_me,
	 	sum( CASE WHEN aml.amount_currency<0 THEN -1* aml.amount_currency ELSE 0 END) as abono_me,
	 	Null::integer as nro_asiento,
	 	aa.id as aa_id,
	 	0 as ordenamiento,
	 	0 as diario_id

		FROM account_move_line aml
		 JOIN account_journal aj ON aj.id = aml.journal_id
		 JOIN account_move am ON am.id = aml.move_id
		 JOIN account_period ap ON ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable  and ap.special = am.fecha_special
		 JOIN account_account aa ON aa.id = aml.account_id
		 LEFT JOIN einvoice_means_payment mp ON mp.id = am.means_payment_it
		 LEFT JOIN res_currency rc ON rc.id = aml.currency_id
		 LEFT JOIN res_partner rp ON rp.id = aml.partner_id
		 LEFT JOIN einvoice_catalog_01 itd ON itd.id = aml.type_document_it
		 LEFT JOIN account_analytic_account aaa ON aaa.id = aml.analytic_account_id
	WHERE periodo_num(ap.name) >= (substring($2::varchar,0,5)||'0')::integer  and periodo_num(ap.name) < $2
	and am.state != 'draft'
	group by aa.id


	) AS T
	order by ordenamiento,fecha,cheque,documento
	
	) AS M;

END;
$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
	""")




class impresion_cheques(models.Model):
	_name ='impresion.cheques'


	@api.multi
	def do_rebuild(self):
		import re
		if 'active_ids' in self.env.context:

			linea = self.env['account.bank.report'].search([('id','=',self.env.context['active_ids'][0])])[0]


			config_print = self.env['config.print.cheques'].search([('journal_id','=',linea.diario_id)])

			txt = ""
			if config_print and len(config_print)>0 and config_print[0]:
				txt = config_print.texto
				fecha_parse = linea.fecha.split('-')
				fecha_dia = None
				fecha_mes = None 
				fecha_anio = None
				if len(fecha_parse[0]) == 4:
					fecha_anio = fecha_parse[0]
					fecha_mes = fecha_parse[1]
					fecha_dia = fecha_parse[2]
				else:
					fecha_anio = fecha_parse[2]
					fecha_mes = fecha_parse[1]
					fecha_dia = fecha_parse[0]

				txt = txt.replace('(A11)', str(fecha_dia) )
				txt = txt.replace('(A12)', str(fecha_mes) )
				txt = txt.replace('(A13)', str(fecha_anio) )

				txt = txt.replace('(A2)', (str( re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1,", "%.2f" % (linea.cargo_mn+ linea.abono_mn) ) ) ).rjust(12) )
				txt = txt.replace('(A3)', str(linea.nombre))
				txt = txt.replace('(A4)', number_to_letter(linea.cargo_mn + linea.abono_mn) )

			else:
				txt = txt+chr(27)+chr(15)+chr(27)+chr(48)			
				txt = txt+"\n"
				txt = txt+"                    "+ linea.fecha + "                " + str( re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1,", "%.2f" % (linea.cargo_mn- linea.abono_mn) ) )+"\n"
				txt = txt+"\n"
				txt = txt+"\n"			
				txt = txt+"\n"
				txt = txt+"     "+ str(linea.nombre) + "\n"
				txt = txt+"     "+ "SON: "+ number_to_letter(linea.cargo_mn + linea.abono_mn) + " *******************" +"\n"
				txt = txt+chr(12)+chr(27)

			self.env['make.txt'].makefile(txt,'chk')



class config_print_cheques(models.Model):
	_name = 'config.print.cheques'

	journal_id = fields.Many2one('account.journal','Banco')
	texto = fields.Text('Formato de Impresión')

	_defaults={
		'texto': chr(27)+chr(15)+chr(27)+chr(48) +"\n"+"                    "+ '(A11)'+ '(A12)'+ '(A13)' + "                " + "(A2)" + "\n"+ "\n"+ "\n"+"     "+ "(A3)" + "\n"+"     "+ "SON: "+ "(A4)"+ " *******************" +"\n"+chr(12)+chr(27)
	}
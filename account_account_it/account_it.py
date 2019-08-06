# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _

class account_patrimony_it(models.Model):
	_name = 'account.patrimony.it'

	name = fields.Char('Tipo de Patrimonio',required=True)

class account_config_settings(models.TransientModel):
	_inherit = 'account.config.settings'

	transfer_account_id = fields.Many2one('account.account',related='company_id.transfer_account_id', domain= lambda self: [('reconcile','=',False),('user_type_id.type','=','liquidity')], help="Cuenta intermedia utilizada al mover dinero desde una cuenta de liquidez a otra")

class account_account(models.Model):
	_inherit='account.account'

	parent_id = fields.Many2one('account.account','Padre')

	tipo_adquisicion_diario = fields.Selection([('1','Mercaderia'),('2','Activo Fijo'),('3','Otros Activo'),('4','Gastos de Educacion, Recreación, Salud, Mantenimiento de Activos'),('5','Otros no incluidos en 4')],'Tipo de Adquisición')	
	#patrimony_type = fields.Selection([('1','CAPITAL'),('2','CAPITAL ADICIONAL'),('3','PARTI. PATR. TRAB.'),('4','RESERVA LEGAL'),('5','OTRAS RESERVAS'),('6','RESULTADOS ACUMULADOS')],'Tipo Patrimonio Neto')
	patrimony_id = fields.Many2one('account.patrimony.it','Tipo Patrimonio Neto')

	account_analytic_account_moorage_id = fields.Many2one('account.account',string ="Amarre al Haber",index = True)
	account_analytic_account_moorage_debit_id = fields.Many2one('account.account',string ="Amarre al Debe",index = True)
	check_moorage = fields.Boolean(string="Tiene Destino")


	clasification_sheet = fields.Selection([('1','Situación Financiera'),
									('2','Resultados por Naturaleza'),
									('3','Resultados por Función'),
									('6','Resultados'),
									('4','Cuenta de Orden'),
									('5','Cuenta de Mayor')
									],'Clasificación Hoja de Trabajo')
	level_sheet = fields.Selection([('1','Cuentas de Balance'),
									('2','Cuentas de Registro')
									],'Nivel')

	code_sunat = fields.Char('CODIGO SUNAT')

	cashbank_code = fields.Char('Code', size=100)
	cashbank_number = fields.Char('Número de Cuenta',size=100)
	cashbank_financy = fields.Char('Entidad Financiera', size=100)

	fefectivo_id = fields.Many2one('account.config.efective',string='F. Efectivo')

	type_it = fields.Many2one('account.account.type.it','Tipo Estado Financiero')


class account_account_type_it(models.Model):
	_name = 'account.account.type.it'

	name = fields.Char('Nombre')
	code = fields.Char('Codigo')

	order_balance = fields.Integer(string='Orden')
	group_balance = fields.Selection([('B1','Activo Corriente'),
									('B2','Activo no Corriente'),
									('B3','Pasivo Corriente'),
									('B4','Pasivo no Corriente'),
									('B5','Patrimonio')									
									],'Grupo Balance')

	order_nature = fields.Integer(string='Orden')
	group_nature = fields.Selection([('N1','Grupo 1'),
									('N2','Grupo 2'),
									('N3','Grupo 3'),
									('N4','Grupo 4'),
									('N5','Grupo 5'),
									('N6','Grupo 6'),
									('N7','Grupo 7'),
									('N8','Grupo 8')
									],'Grupo Naturaleza')

	order_function = fields.Integer(string='Orden')
	group_function = fields.Selection([('F1','Grupo 1'),
									('F2','Grupo 2'),
									('F3','Grupo 3'),
									('F4','Grupo 4'),
									('F5','Grupo 5'),
									('F6','Grupo 6')
									],'Grupo Función')


class account_account_type(models.Model):
	_inherit = 'account.account.type'

	type = fields.Selection([
		('view', 'Vista'),
		('other', 'Regular'),
		('receivable', 'Por Cobrar'),
		('payable', 'A Pagar'),
		('liquidity', 'Liquidez'),
	], required=True, default='other')

	



# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
from openerp.exceptions import  Warning

class log_maintenace_db(models.Model):
	_name = 'log.maintenace.db'

	backup = fields.Boolean('Backup',default=False)
	obs_backup = fields.Char('Observacion Backup')

	vacuum = fields.Boolean('Vacum',default=False)
	obs_vacuum = fields.Char('Observacion Vacum')

	reindex = fields.Boolean('reindex',default=False)
	obs_reindex = fields.Char('Observacion reindex')


	date = fields.Date('fecha')

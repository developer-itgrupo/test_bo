# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import base64
from openerp.osv import osv
from datetime import *
from decimal import *

class corrector_rendicion(models.Model):
	_name = 'corrector.rendicion'

	@api.one
	def do_rebuild(self):
		param = self.env['main.parameter'].search([])[0]
		self.env.cr.execute("""

			update account_move_line set partner_id = T.empleado,type_document_it = null,nro_comprobante = T.name  from 
(select a1.id,a1.rendicion_id,a1.partner_id,a2.empleado,a2.name from account_move_line  a1
left  join account_rendicion_it a2 on a2.id = a1. rendicion_id
where account_id in ("""+str(param.deliver_account_mn.id)+""","""+str(param.deliver_account_me.id)+""")
order by rendicion_id) T where T.id = account_move_line.id;



update account_move_line set partner_id = T.empleado, type_document_it = null, nro_comprobante = T.name from (
select a1.name, a1.empleado, a3.id
from account_rendicion_it a1
inner join account_move a2 on a2.id = a1.asiento2
inner join account_move_line a3 on a3.move_id = a2.id and a3.account_id in ("""+str(param.deliver_account_mn.id)+""","""+str(param.deliver_account_me.id)+""") ) T where  T.id = account_move_line.id;

			""")
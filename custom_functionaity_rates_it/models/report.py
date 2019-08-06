class CrmReport(models.TransientModel):
    _name = 'crm.won.lost.report'
    sales_person = fields.Many2one('res.users', string="Sales Person")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date', default=fields.Date.today)
 
    def print_xls_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids)[0]
        return {'type': 'ir.actions.report.xml',
                'report_name': 'crm_won_lost_report.report_crm_won_lost_report.xlsx',
                'datas': data
                }
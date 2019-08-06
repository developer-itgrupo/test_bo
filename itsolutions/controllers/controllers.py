# -*- coding: utf-8 -*-
from odoo import http

# class Itsolutions(http.Controller):
#     @http.route('/itsolutions/itsolutions/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/itsolutions/itsolutions/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('itsolutions.listing', {
#             'root': '/itsolutions/itsolutions',
#             'objects': http.request.env['itsolutions.itsolutions'].search([]),
#         })

#     @http.route('/itsolutions/itsolutions/objects/<model("itsolutions.itsolutions"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('itsolutions.object', {
#             'object': obj
#         })
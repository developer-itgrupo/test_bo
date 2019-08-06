# -*- coding: utf-8 -*-
from odoo import http

# class ExchangeDiffIt(http.Controller):
#     @http.route('/exchange_diff_it/exchange_diff_it/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/exchange_diff_it/exchange_diff_it/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('exchange_diff_it.listing', {
#             'root': '/exchange_diff_it/exchange_diff_it',
#             'objects': http.request.env['exchange_diff_it.exchange_diff_it'].search([]),
#         })

#     @http.route('/exchange_diff_it/exchange_diff_it/objects/<model("exchange_diff_it.exchange_diff_it"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('exchange_diff_it.object', {
#             'object': obj
#         })
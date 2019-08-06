-- View: vst_kardex_fisico_proc_1

-- DROP VIEW vst_kardex_fisico_proc_1;
 DROP VIEW IF EXISTS vst_kardex_fisico_proc_1 CASCADE;
-- View: vst_kardex_fisico_proc_1
-- View: vst_kardex_fisico_proc_1
-- View: vst_kardex_fisico_proc_1
-- View: vst_kardex_fisico_proc_1

-- DROP VIEW vst_kardex_fisico_proc_1;
-- View: vst_kardex_fisico_proc_1

-- DROP VIEW vst_kardex_fisico_proc_1;
-- View: vst_kardex_fisico_proc_1

-- DROP VIEW vst_kardex_fisico_proc_1;


CREATE OR REPLACE VIEW public.vst_kardex_fisico_proc_1 AS
 SELECT k.origen,
    k.destino,
    k.serial,
    k.nro,
    k.cantidad,
    k.producto,
    k.fecha,
    k.id_origen,
    k.id_destino,
    k.product_id,
    k.id,
    k.categoria,
    k.name,
    k.unidad,
    k.default_code,
    k.price_unit,
    k.currency_rate,
    k.invoice_id,
    k.periodo,
    k.ctanalitica,
    k.operation_type,
    k.doc_type_ope,
    k.category_id,
    k.stock_doc,
    k.type_doc,
    k.numdoc_cuadre,
    k.nro_documento,
    (aa_cp.code::text || ' - '::text) || aa_cp.name::text AS product_account
   FROM ( SELECT origen.complete_name AS origen,
            destino.complete_name AS destino,
                CASE
                    WHEN vst_stock_move.location_id IS NULL THEN getserial(vst_stock_move.name)
                    ELSE getserial(account_invoice.reference)
                END AS serial,
                CASE
                    WHEN vst_stock_move.location_id IS NULL THEN getnumber(vst_stock_move.name)
                    ELSE
                    CASE
                        WHEN vst_stock_move.invoice_id <> 0 AND vst_stock_move.location_id IS NOT NULL THEN getnumber(account_invoice.reference)::character varying(10)
                        ELSE ''::character varying
                    END
                END AS nro,
            vst_stock_move.product_qty AS cantidad,
            product_name.name::character varying AS producto,
            vst_stock_move.date AS fecha,
            vst_stock_move.location_id AS id_origen,
            vst_stock_move.location_dest_id AS id_destino,
            vst_stock_move.product_id,
            vst_stock_move.id,
            product_category.name AS categoria,
                CASE
                    WHEN vst_stock_move.invoice_id = 0 OR vst_stock_move.invoice_id IS NULL THEN res_partner.name
                    ELSE rp.name
                END AS name,
            uomt.name AS unidad,
            product_product.default_code,
                CASE
                    WHEN rc.name::text = 'PEN'::text THEN vst_stock_move.price_unit
                    ELSE vst_stock_move.price_unit * COALESCE(rcr.type_sale, 1::numeric)::double precision
                END AS price_unit,
            rcr.rate AS currency_rate,
            vst_stock_move.invoice_id,
            account_period.name AS periodo,
            account_analytic_account.name AS ctanalitica,
            lpad(vst_stock_move.guia::text, 2, '0'::text)::character varying AS operation_type,
            lpad(
                CASE
                    WHEN vst_stock_move.location_id IS NULL THEN it_type_document2.code
                    ELSE it_type_document.code
                END::text, 2, '0'::text) AS doc_type_ope,
            product_category.id AS category_id,
                CASE
                    WHEN vst_stock_move.location_id IS NULL THEN ''::character varying
                    ELSE vst_stock_move.name
                END AS stock_doc,
                CASE
                    WHEN vst_stock_move.location_id IS NULL AND vst_stock_move.picking_type_id IS NULL THEN it_type_document2.code
                    ELSE
                    CASE
                        WHEN vst_stock_move.location_id IS NULL THEN it_type_document3.code
                        ELSE it_type_document.code
                    END
                END AS type_doc,
                CASE
                    WHEN vst_stock_move.location_id IS NULL THEN vst_stock_move.name
                    ELSE COALESCE(account_invoice.reference, ''::character varying)
                END AS numdoc_cuadre,
            res_partner.nro_documento
           FROM ( SELECT vst_kardex_fisico.product_uom,
                    vst_kardex_fisico.move_dest_id,
                    vst_kardex_fisico.price_unit,
                    vst_kardex_fisico.product_qty,
                    vst_kardex_fisico.location_id,
                    vst_kardex_fisico.location_dest_id,
                    vst_kardex_fisico.picking_type_id,
                    vst_kardex_fisico.product_id,
                    vst_kardex_fisico.picking_id,
                    vst_kardex_fisico.invoice_id,
                    vst_kardex_fisico.date,
                    vst_kardex_fisico.name,
                    vst_kardex_fisico.partner_id,
                    vst_kardex_fisico.guia,
                    vst_kardex_fisico.analitic_id,
                    vst_kardex_fisico.id,
                    vst_kardex_fisico.default_code,
                    vst_kardex_fisico.estado
                   FROM vst_kardex_fisico
                UNION ALL
                 SELECT vst_kardex_fisico_gastos_vinculados.product_uom,
                    vst_kardex_fisico_gastos_vinculados.move_dest_id,
                    vst_kardex_fisico_gastos_vinculados.price_unit,
                    vst_kardex_fisico_gastos_vinculados.product_qty,
                    vst_kardex_fisico_gastos_vinculados.location_id,
                    vst_kardex_fisico_gastos_vinculados.location_dest_id,
                    vst_kardex_fisico_gastos_vinculados.picking_type_id,
                    vst_kardex_fisico_gastos_vinculados.product_id,
                    vst_kardex_fisico_gastos_vinculados.picking_id,
                    vst_kardex_fisico_gastos_vinculados.invoice_id,
                    vst_kardex_fisico_gastos_vinculados.date,
                    vst_kardex_fisico_gastos_vinculados.name,
                    vst_kardex_fisico_gastos_vinculados.partner_id,
                    vst_kardex_fisico_gastos_vinculados.guia,
                    vst_kardex_fisico_gastos_vinculados.analitic_id,
                    vst_kardex_fisico_gastos_vinculados.id,
                    vst_kardex_fisico_gastos_vinculados.default_code,
                    vst_kardex_fisico_gastos_vinculados.estado
                   FROM vst_kardex_fisico_gastos_vinculados) vst_stock_move
             JOIN product_product ON vst_stock_move.product_id = product_product.id
             JOIN ( SELECT pp.id,
                    pt.name::text || COALESCE((' ('::text || string_agg(pav.name::text, ', '::text)) || ')'::text, ''::text) AS name
                   FROM product_product pp
                     JOIN product_template pt ON pt.id = pp.product_tmpl_id
                     LEFT JOIN product_attribute_value_product_product_rel pavpp ON pavpp.product_product_id = pp.id
                     LEFT JOIN product_attribute_value pav ON pav.id = pavpp.product_attribute_value_id
                  GROUP BY pp.id, pt.name) product_name ON product_name.id = product_product.id
             JOIN product_template ON product_product.product_tmpl_id = product_template.id
             JOIN product_category ON product_template.categ_id = product_category.id
             JOIN product_uom ON vst_stock_move.product_uom = product_uom.id
             JOIN product_uom uomt ON uomt.id =
                CASE
                    WHEN product_template.unidad_kardex IS NOT NULL THEN product_template.unidad_kardex
                    ELSE product_template.uom_id
                END
             LEFT JOIN account_invoice ON account_invoice.id = vst_stock_move.invoice_id
             LEFT JOIN account_analytic_account ON vst_stock_move.analitic_id = account_analytic_account.id
             LEFT JOIN stock_location origen ON vst_stock_move.location_id = origen.id
             LEFT JOIN stock_location destino ON vst_stock_move.location_dest_id = destino.id
             LEFT JOIN res_partner ON vst_stock_move.partner_id = res_partner.id
             LEFT JOIN res_partner rp ON account_invoice.partner_id = rp.id
             LEFT JOIN stock_move sm ON sm.id = vst_stock_move.id
             LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
             LEFT JOIN purchase_order_line pol ON pol.id = sm.purchase_line_id
             LEFT JOIN purchase_order po ON po.id = pol.order_id
             LEFT JOIN sale_order so ON so.procurement_group_id = sp.group_id
             LEFT JOIN product_pricelist pplist ON pplist.id = so.pricelist_id
             LEFT JOIN res_currency rc ON rc.id =
                CASE
                    WHEN pol.id IS NOT NULL THEN po.currency_id
                    ELSE pplist.currency_id
                END
             LEFT JOIN res_currency_rate rcr ON rcr.name = vst_stock_move.date::date AND rcr.currency_id = rc.id
             LEFT JOIN account_period ON account_period.date_start <= vst_stock_move.date AND account_period.date_stop >= vst_stock_move.date AND COALESCE(account_period.special, false) = false
             LEFT JOIN account_move_line aml ON aml.id = vst_stock_move.invoice_id
             LEFT JOIN gastos_vinculados_distribucion_detalle gvdd ON gvdd.id = vst_stock_move.invoice_id
             LEFT JOIN einvoice_catalog_01 it_type_document ON account_invoice.it_type_document = it_type_document.id
             LEFT JOIN einvoice_catalog_01 it_type_document2 ON aml.type_document_it = it_type_document2.id
             LEFT JOIN einvoice_catalog_01 it_type_document3 ON gvdd.tipo = it_type_document3.id
             LEFT JOIN ir_property ipx ON ipx.res_id::text = ('product.template,'::text || product_template.id) AND ipx.name::text = 'cost_method'::text
          WHERE vst_stock_move.estado::text = 'done'::text) k
     LEFT JOIN ( SELECT "substring"(ir_property.res_id::text, "position"(ir_property.res_id::text, ','::text) + 1)::integer AS categ_id,
            "substring"(ir_property.value_reference::text, "position"(ir_property.value_reference::text, ','::text) + 1)::integer AS account_id
           FROM ir_property
          WHERE ir_property.name::text = 'property_stock_valuation_account_id'::text) j ON k.category_id = j.categ_id
     LEFT JOIN account_account aa_cp ON j.account_id = aa_cp.id;

ALTER TABLE public.vst_kardex_fisico_proc_1
    OWNER TO openpg;

GRANT ALL ON TABLE public.vst_kardex_fisico_proc_1 TO openpg;

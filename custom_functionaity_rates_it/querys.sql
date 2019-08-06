--QUERY PARA LA CREACION Y ELIMINADO DE LA LISTA DE TARIFAS
Create or replace function public.get_lista(
				IN tp_op integer,
				IN id_lista integer,
				IN id_cat integer)
				RETURNS TABLE(id integer) AS
				$BODY$
				BEGIN
				IF tp_op = 1 THEN
				--Para agregar 
				IF id_cat=0 THEN
				RETURN QUERY
				SELECT product_product.id FROM product_product
				WHERE product_product.id 
				NOT IN (SELECT product_id FROM product_pricelist_item 
				WHERE product_pricelist_item.pricelist_id = id_lista);
				ELSE 
				RETURN QUERY
				SELECT product_product.id FROM product_product
				INNER JOIN product_template 
				ON product_template.id = product_product.product_tmpl_id

				WHERE product_template.categ_id = id_cat 
				AND product_product.id NOT IN (SELECT product_id FROM product_pricelist_item 
				WHERE product_pricelist_item.pricelist_id = id_lista);
				END IF;
				END IF;
				IF tp_op = 2 THEN
				--Para borrar 
				IF id_cat=0 THEN
				--RETURN NULL
				DELETE  FROM product_pricelist_item 
				WHERE product_pricelist_item.pricelist_id = id_lista;

				ELSE 
				--RETURN NULL
				DELETE  FROM product_pricelist_item 
				WHERE product_pricelist_item.pricelist_id = id_lista 
				AND product_pricelist_item.product_id IN (SELECT product_product.id FROM product_product
				INNER JOIN product_template 
				ON product_template.id = product_product.product_tmpl_id
				WHERE product_template.categ_id = id_cat );
				END IF;
				END IF;
				     
				END; $BODY$
				LANGUAGE plpgsql VOLATILE
				COST 100
				ROWS 1000;
				ALTER FUNCTION public.get_lista(integer, integer, integer)
				OWNER TO openpg;
			



--LOS 3 SIGUIENTES QUERYS SE UTILIZAN PARA PODER EL ULTIMO PRECIO DE COMPRA
create or replace view public.vst_last_fecha as 
				select purchase_order_line.product_id,
				max(purchase_order.date_order) as last_fecha,res_currency.symbol as simbolo
				from purchase_order_line
				join purchase_order on purchase_order.id = purchase_order_line.order_id
				join res_currency on res_currency.id = purchase_order.currency_id
				where purchase_order.state = 'purchase' or purchase_order.state = 'done'
				group by purchase_order_line.product_id,res_currency.symbol;

				alter table public.vst_last_fecha
				owner to openpg;




	
create or replace view public.vst_oc as 
				select purchase_order_line.product_id,
				purchase_order.date_order,
				purchase_order_line.price_unit
				from purchase_order_line
				join purchase_order on purchase_order.id = purchase_order_line.order_id;

				alter table public.vst_oc
				  owner to openpg;


create or replace view public.vst_ultimos_precios_compra as 
				select vst_oc.product_id,
				vst_oc.date_order,
				vst_oc.price_unit,
				vst_last_fecha.simbolo
				from vst_last_fecha
				join vst_oc on vst_oc.product_id = vst_last_fecha.product_id and vst_oc.date_order = vst_last_fecha.last_fecha
				order by vst_last_fecha.product_id;

				alter table public.vst_ultimos_precios_compra
				owner to openpg;


				
--QUERY PARA LA EXPORTACION A CSV DE LOS ELEMTNOS DE TARIFA
CREATE OR REPLACE FUNCTION public.get_rep_tarifa(IN tarifa_id integer)
  RETURNS TABLE(id_odoo integer, codigo character varying, producto character varying, moneda character varying, precio numeric, costo_promedio double precision, ultima_compra numeric) AS
$BODY$
BEGIN
RETURN QUERY
SELECT product_product.id AS "ID_ODOO" ,product_product.default_code AS "Codigo",product_product.campo_name_get AS "Producto",
res_currency.name as "Moneda",product_pricelist_item.fixed_price as "Precio",p_promedio.costo_promedio as "Costo_Promedio",
vst_ultimos_precios_compra.price_unit as "Ultima_Compra"
FROM product_product
JOIN product_pricelist_item ON product_pricelist_item.product_id = product_product.id
JOIN product_pricelist ON product_pricelist.id = product_pricelist_item.pricelist_id
JOIN res_currency ON res_currency.id = product_pricelist.currency_id
LEFT JOIN vst_ultimos_precios_compra ON vst_ultimos_precios_compra.product_id = product_product.id
LEFT JOIN(SELECT  substr (res_id, 17) as product_id, value_float as costo_promedio
FROM ir_property
WHERE name='standard_price') p_promedio ON cast(p_promedio.product_id AS INTEGER) = product_product.id
WHERE product_pricelist_item.pricelist_id = tarifa_id;
				     
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION public.get_rep_tarifa(integer)
  OWNER TO openpg;



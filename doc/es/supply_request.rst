#:after:stock_supply_request/supply_request:paragraph:campos_lineas#

Si el producto no esta marcado cómo que *Puede ser comprado*, se nos marcará
el campo |to_produce|.

.. |to_produce| field:: stock.supply_request.line/to_produce

#:after:stock_supply_request/supply_request:paragraph:confirm#

Si la línea es |to_produce| se crea la producción en estado *Borrador* y con
la |planned_date| de la línea.

Podremos consultar el |production_state| en cada línea de sol·licitud, que
podrá tener los siguientes valores:

 * *Pendiente*: La producción aún no se ha iniciado
 * *En progreso*: Los materiales se estan produciendo; la producción esta en espera, 
   reservada o ejecutándose.
 * *Realizado*: La producción se ha realizado, y tenemos los materiales en el
   almacén de origen.

.. |planned_date| field:: production/planned_date
.. |production_state| field:: stock.supply_request.line/production_state

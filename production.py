# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, Workflow, fields
from trytond.pool import Pool, PoolMeta

__all__ = ['Production']
__metaclass__ = PoolMeta


class Production:
    __name__ = 'production'

    from_supply_request = fields.Function(
        fields.Boolean('From Supply Request', on_change_with=['origin']),
        'on_change_with_from_supply_request')

    @classmethod
    def __setup__(cls):
        super(Production, cls).__setup__()
        cls._error_messages.update({
            'invalid_product_origin': 'The product of the production "%s" is '
                'different than its origin Supply Request.',
            'production_related_to_supply_request': 'The production '
                '"%(production)s" is relate the supply request "%(request)s" '
                'so you can\'t delete it.',
            })

    def on_change_with_from_supply_request(self, name=None):
        pool = Pool()
        SupplyRequestLine = pool.get('stock.supply_request.line')
        return self.origin and isinstance(self.origin, SupplyRequestLine)

    @classmethod
    def _get_origin(cls):
        res = super(Production, cls)._get_origin()
        return res + ['stock.supply_request.line']

    @classmethod
    def validate(cls, productions):
        super(Production, cls).validate(productions)
        for production in productions:
            if production.from_supply_request:
                production.check_origin_supply_request()

    def check_origin_supply_request(self):
        if self.origin.product.id != self.product.id:
            self.raise_user_error('invalid_product_origin', self.rec_name)

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def done(cls, productions):
        super(Production, cls).done(productions)
        for production in productions:
            if production.from_supply_request:
                for output in production.outputs:
                    if output.product.id == production.product.id:
                        production._assign_reservation(output)

    def _assign_reservation(self, main_output):
        pool = Pool()
        Move = pool.get('stock.move')

        reservation = self.origin.move
        reservation.from_location = main_output.to_location
        if getattr(main_output, 'lot', False):
            reservation.lot = main_output.lot
        reservation.save()
        return Move.assign_try([reservation])

    @classmethod
    def write(cls, productions, vals):
        pool = Pool()
        Uom = pool.get('product.uom')

        super(Production, cls).write(productions, vals)
        if 'quantity' in vals or 'uom' in vals:
            for production in productions:
                if not production.from_supply_request:
                    continue

                quantity = vals.get('quantity', production.quantity)
                uom = vals.get('uom', production.uom)
                reservation_move = production.origin.move
                if uom != reservation_move.uom:
                    quantity = Uom.compute_qty(uom, quantity,
                        reservation_move.uom)
                if quantity != reservation_move.quantity:
                    reservation_move.quantity = quantity
                    reservation_move.save()

    @classmethod
    def delete(cls, productions):
        pool = Pool()
        SupplyRequestLine = pool.get('stock.supply_request.line')

        for production in productions:
            request_line = SupplyRequestLine.search([
                    ('production', '=', production.id),
                    ])
            if request_line:
                cls.raise_user_error('production_related_to_supply_request', {
                        'production': production.rec_name,
                        'request': request_line[0].request.rec_name,
                        })
        super(Production, cls).delete(productions)

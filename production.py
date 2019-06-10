# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, Workflow, fields
from trytond.pool import Pool, PoolMeta
from trytond.exceptions import UserError
from trytond.i18n import gettext

__all__ = ['Production']


class Production(metaclass=PoolMeta):
    __name__ = 'production'

    from_supply_request = fields.Function(fields.Boolean(
            'From Supply Request'),
        'on_change_with_from_supply_request')

    @fields.depends('origin')
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
            production.check_origin_supply_request()

    def check_origin_supply_request(self):
        if (self.from_supply_request and
                self.origin.product.id != self.product.id):
            raise UserError(gettext(
                    'production_supply_request.msg_invalid_product_origin',
                    production=self.rec_name))

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
    def write(cls, *args):
        pool = Pool()
        Uom = pool.get('product.uom')

        super(Production, cls).write(*args)
        actions = iter(args)
        for productions, vals in zip(actions, actions):
            if 'quantity' in vals or 'uom' in vals:
                for production in productions:
                    if not production.from_supply_request:
                        continue

                    quantity = vals.get('quantity', production.quantity)
                    if vals.get('uom'):
                        uom = Uom(vals['uom'])
                    else:
                        uom = production.uom
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
                raise UserError(gettext('production_supply_request.'
                        'msg_production_related_to_supply_request',
                        production=production.rec_name,
                        request=request_line[0].request.rec_name,
                        ))
        super(Production, cls).delete(productions)

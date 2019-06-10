# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from trytond.model import ModelView, Workflow, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import And, Equal, Eval, Not
from trytond.transaction import Transaction

__all__ = ['SupplyRequest', 'SupplyRequestLine']


def prepare_write_vals(values):
    if isinstance(values, dict):
        if set(values.keys()) <= set(['add', 'remove']):
            res = []
            if 'add' in values.keys():
                res.append(('create',
                        prepare_write_vals([v[1] for v in values['add']])))
            if 'remove' in values.keys():
                res.append(('delete', values['remove']))
        else:
            res = {}
            for key, value in values.items():
                if 'rec_name' in key or key == 'id':
                    continue
                value = prepare_write_vals(value)
                if value is not None:
                    res[key] = value
        return res or None
    elif isinstance(values, list):
        return [prepare_write_vals(v) for v in values]
    return values


class SupplyRequest(metaclass=PoolMeta):
    __name__ = 'stock.supply_request'

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, requests):
        super(SupplyRequest, cls).confirm(requests)
        for request in requests:
            for line in request.lines:
                if line.to_produce:
                    with Transaction().set_user(0, set_context=True):
                        production = line.get_production()
                        production.on_change_bom()
                        production.save()

                    line.production = production
                    line.save()


class SupplyRequestLine(metaclass=PoolMeta):
    __name__ = 'stock.supply_request.line'

    to_produce = fields.Function(fields.Boolean('To Produce'),
        'on_change_with_to_produce')
    production = fields.Many2One('production', 'Production', readonly=True,
        domain=[
            ('product', '=', Eval('product')),
            #('origin', '=', 'stock.supply_request.line', Eval('id')),
            ],
        states={
            'required': And(Eval('to_produce', False),
                Equal(Eval('_parent_request.state'), 'confirmed')),
            'invisible': Not(Eval('to_produce', False)),
            }, depends=['to_produce', 'product', 'id'])
    production_state = fields.Function(fields.Selection([
                ('pending', 'Pending'),
                ('in_progress', 'In Progress'),
                ('done', 'Done'),
                ('cancel', 'Canceled'),
                ], 'Production State',
            states={
                'invisible': Not(Eval('to_produce', False)),
                }, depends=['to_produce']),
        'get_production_state')

    @fields.depends('product')
    def on_change_with_to_produce(self, name=None):
        if not self.product:
            return False
        if not getattr(self.product, 'purchasable', False):
            return True
        return not self.product.purchasable

    def get_production_state(self, name):
        if (not self.production
                or self.production.state in ('request', 'draft')):
            return 'pending'
        if self.production.state in ('done', 'cancel'):
            return self.production.state
        return 'in_progress'

    def get_production(self):
        '''
        Return the production for the line
        '''
        Production = Pool().get('production')

        production = Production(
            reference=self.request.rec_name,
            planned_date=self.request.date.date(),
            planned_start_date=self.request.date.date(),
            company=self.request.company,
            warehouse=self.request.from_warehouse,
            location=self.request.from_warehouse.production_location,
            product=self.product,
            bom=self._production_bom(),
            uom=self.unit,
            quantity=self.quantity,
            origin=self,
            state='draft')
        return production

    def _production_bom(self):
        return self.product.boms and self.product.boms[0].bom or None

    @classmethod
    def copy(cls, lines, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default['production'] = None
        return super(SupplyRequestLine, cls).copy(lines, default=default)

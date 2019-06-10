#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.

from trytond.pool import Pool
from . import production
from . import supply_request


def register():
    Pool.register(
        production.Production,
        supply_request.SupplyRequest,
        supply_request.SupplyRequestLine,
        module='production_supply_request', type_='model')

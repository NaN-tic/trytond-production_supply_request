#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.

from trytond.pool import Pool
from .production import *
from .supply_request import *


def register():
    Pool.register(
        Production,
        SupplyRequest,
        SupplyRequestLine,
        module='production_supply_request', type_='model')

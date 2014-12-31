# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .guarantee import *


def register():
    Pool.register(
        Asset,
        Guarantee,
        SaleLine,
        InvoiceLine,
        module='asset_guarantee', type_='model')

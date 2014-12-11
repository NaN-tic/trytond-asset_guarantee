# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Asset', 'Guarantee', 'SaleLine']
__metaclass__ = PoolMeta


class Asset:
    __name__ = 'asset'
    guarantee_resource = fields.Function(fields.Char('Resource'),
        'on_change_with_guarantee_resource')
    guarantee = fields.Many2One('guarantee.guarantee', 'Guarantee',
        context={
            'document': Eval('guarantee_resource'),
            },
        depends=['guarantee_resource'])

    @fields.depends('sale')
    def on_change_with_guarantee_resource(self, name=None):
        if self.id:
            return str(self)
        return ''


class Guarantee:
    __name__ = 'guarantee.guarantee'

    @classmethod
    def _get_origin(cls):
        origins = super(Guarantee, cls)._get_origin()
        origins.append('asset')
        return origins

    @staticmethod
    def default_document():
        return Transaction().context.get('document')


class SaleLine:
    __name__ = 'sale.line'
    asset = fields.Many2One('asset', 'Asset',
        states={
            'invisible': Eval('type') != 'line',
        })

    @fields.depends('asset')
    def on_change_with_line_in_guarantee(self, name=None):
        if self.asset and self.asset.guarantee:
            self.guarantee = self.asset.guarantee
        return super(SaleLine, self).on_change_with_line_in_guarantee(name)

    @fields.depends('asset', methods=['guarantee'])
    def on_change_asset(self):
        changes = {}
        if self.asset and self.asset.guarantee:
            changes['guarantee'] = self.asset.guarantee.id
            changes['guarantee.rec_name'] = self.asset.guarantee.rec_name
            self.guarantee = self.asset.guarantee
            changes.update(self.on_change_guarantee())
        return changes

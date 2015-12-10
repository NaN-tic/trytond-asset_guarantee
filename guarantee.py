# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from itertools import groupby
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Asset', 'Guarantee', 'Sale', 'SaleLine', 'InvoiceLine']
__metaclass__ = PoolMeta


class Asset:
    __name__ = 'asset'
    guarantees = fields.One2Many('guarantee.guarantee', 'document',
        'Guarantees')


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


class Sale:
    __name__ = 'sale.sale'

    guarantee_type = fields.Many2One('guarantee.type', 'Guarantee Type',
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state'])

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()
        if not 'asset' in cls.lines.depends:
            cls.lines.context.update({
                    'asset': Eval('asset'),
                    'sale_date': Eval('sale_date'),
                    })
            cls.lines.depends.append('asset')
            cls.lines.depends.append('sale_date')

    @classmethod
    def process(cls, sales):
        pool = Pool()
        Guarantee = pool.get('guarantee.guarantee')
        super(Sale, cls).process(sales)
        guarantees = []
        for sale in sales:
            guarantees += sale.get_asset_guarantees()
        if guarantees:
            to_create = []
            for key, grouped_guarantees in groupby(guarantees,
                    key=cls._group_asset_guarantees_key):
                guarantee = grouped_guarantees.next()
                for g in grouped_guarantees:
                    guarantee.sale_lines += g.sale_lines
                to_create.append(guarantee._save_values)
            Guarantee.create(to_create)

    def get_asset_guarantees(self):
        guarantees = []
        if not self.guarantee_type:
            return guarantees
        for line in self.lines:
            guarantees += line.get_asset_guarantees()
        return guarantees

    @classmethod
    def _group_asset_guarantees_key(cls, guarantee):
        'The key to group guarantees created by sale'
        return ({l.sale for l in guarantee.sale_lines}, guarantee.document)


class SaleLine:
    __name__ = 'sale.line'

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        cls.line_in_guarantee.on_change_with.add('asset_used')

    @staticmethod
    def default_guarantee():
        pool = Pool()
        Date = pool.get('ir.date')
        Asset = pool.get('asset')
        today = Date.today()
        context = Transaction().context
        asset_id = context.get('asset')
        if asset_id:
            asset = Asset(asset_id)
            sale_date = context.get('sale_date') or today
            for guarantee in asset.guarantees:
                if guarantee.applies_for_date(sale_date):
                    return guarantee.id

    def get_asset_guarantees(self):
        pool = Pool()
        Guarantee = pool.get('guarantee.guarantee')
        if (not self.product or self.product.type == 'service' or
                not self.asset_used or not self.move_done or
                not self.quantity
                or all(m.state == 'cancel' for m in self.moves)):
            return []
        start_date = max(m.effective_date for m in self.moves
            if m.state != 'cancel')
        guarantee = Guarantee()
        guarantee.party = self.sale.party
        guarantee.document = str(self.asset_used)
        guarantee.type = self.sale.guarantee_type
        guarantee.start_date = start_date
        guarantee.end_date = guarantee.on_change_with_end_date()
        guarantee.sale_lines = [self]
        guarantee.state = 'draft'
        return [guarantee]


class InvoiceLine:
    __name__ = 'account.invoice.line'

    @classmethod
    def __setup__(cls):
        super(InvoiceLine, cls).__setup__()
        cls.line_in_guarantee.on_change_with.add('invoice_asset')

    @fields.depends('invoice_asset', '_parent_invoice.invoice_date',
        methods=['guarantee'])
    def on_change_invoice_asset(self):
        pool = Pool()
        Date = pool.get('ir.date')
        today = Date.today()
        changes = {}
        if self.invoice_asset and self.invoice_asset.guarantees:
            invoice_date = self.invoice.invoice_date or today
            for guarantee in self.invoice_asset.guarantees:
                if guarantee.applies_for_date(invoice_date):
                    changes['guarantee'] = guarantee.id
                    changes['guarantee.rec_name'] = guarantee.rec_name
                    self.guarantee = guarantee
                    changes.update(self.on_change_guarantee())
                    changes.update({
                            'line_in_guarantee': (
                                self.on_change_with_line_in_guarantee()),
                            })
                    break
        changes.update(self.on_change_guarantee())
        return changes

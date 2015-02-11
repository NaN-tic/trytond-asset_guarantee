========================
Asset Guarantee Scenario
========================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()
    >>> tomorrow = today + relativedelta(days=1)

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install sale::

    >>> Module = Model.get('ir.module.module')
    >>> sale_module, = Module.find([('name', '=', 'asset_guarantee')])
    >>> Module.install([sale_module.id], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> currencies = Currency.find([('code', '=', 'USD')])
    >>> if not currencies:
    ...     currency = Currency(name='U.S. Dollar', symbol='$', code='USD',
    ...         rounding=Decimal('0.01'), mon_grouping='[3, 3, 0]',
    ...         mon_decimal_point='.', mon_thousands_sep=',')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Dunder Mifflin')
    >>> party.save()
    >>> company.party = party
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find([])

Reload the context::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> config._context = User.get_preferences(True, config.context)

Create fiscal year::

    >>> FiscalYear = Model.get('account.fiscalyear')
    >>> Sequence = Model.get('ir.sequence')
    >>> SequenceStrict = Model.get('ir.sequence.strict')
    >>> fiscalyear = FiscalYear(name=str(today.year))
    >>> fiscalyear.start_date = today + relativedelta(month=1, day=1)
    >>> fiscalyear.end_date = today + relativedelta(month=12, day=31)
    >>> fiscalyear.company = company
    >>> post_move_seq = Sequence(name=str(today.year), code='account.move',
    ...     company=company)
    >>> post_move_seq.save()
    >>> fiscalyear.post_move_sequence = post_move_seq
    >>> invoice_seq = SequenceStrict(name=str(today.year),
    ...     code='account.invoice', company=company)
    >>> invoice_seq.save()
    >>> fiscalyear.out_invoice_sequence = invoice_seq
    >>> fiscalyear.in_invoice_sequence = invoice_seq
    >>> fiscalyear.out_credit_note_sequence = invoice_seq
    >>> fiscalyear.in_credit_note_sequence = invoice_seq
    >>> fiscalyear.save()
    >>> FiscalYear.create_period([fiscalyear.id], config.context)

Create chart of accounts::

    >>> AccountTemplate = Model.get('account.account.template')
    >>> Account = Model.get('account.account')
    >>> Journal = Model.get('account.journal')
    >>> account_template, = AccountTemplate.find([('parent', '=', None)])
    >>> create_chart = Wizard('account.create_chart')
    >>> create_chart.execute('account')
    >>> create_chart.form.account_template = account_template
    >>> create_chart.form.company = company
    >>> create_chart.execute('create_account')
    >>> receivable, = Account.find([
    ...         ('kind', '=', 'receivable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> payable, = Account.find([
    ...         ('kind', '=', 'payable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> revenue, = Account.find([
    ...         ('kind', '=', 'revenue'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> expense, = Account.find([
    ...         ('kind', '=', 'expense'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> create_chart.form.account_receivable = receivable
    >>> create_chart.form.account_payable = payable
    >>> create_chart.execute('create_properties')
    >>> cash, = Account.find([
    ...         ('kind', '=', 'other'),
    ...         ('name', '=', 'Main Cash'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> cash_journal, = Journal.find([('type', '=', 'cash')])
    >>> cash_journal.credit_account = cash
    >>> cash_journal.debit_account = cash
    >>> cash_journal.save()

Create parties::

    >>> Party = Model.get('party.party')
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create category::

    >>> ProductCategory = Model.get('product.category')
    >>> category = ProductCategory(name='Category')
    >>> category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.category = category
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('8')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> product.template = template
    >>> product.save()
    >>> second_product = Product()
    >>> second_product.template = template
    >>> second_product.save()

    >>> service = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'service'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.salable = True
    >>> template.list_price = Decimal('30')
    >>> template.cost_price = Decimal('10')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> service.template = template
    >>> service.save()

Create payment term::

    >>> PaymentTerm = Model.get('account.invoice.payment_term')
    >>> PaymentTermLine = Model.get('account.invoice.payment_term.line')
    >>> payment_term = PaymentTerm(name='Direct')
    >>> payment_term_line = PaymentTermLine(type='remainder', days=0)
    >>> payment_term.lines.append(payment_term_line)
    >>> payment_term.save()

Create assets::

    >>> Asset = Model.get('asset')
    >>> asset = Asset()
    >>> asset.name = 'Asset'
    >>> asset.product = product
    >>> asset.owner = customer
    >>> asset.save()
    >>> second_asset = Asset()
    >>> second_asset.name = 'Second Asset'
    >>> second_asset.product = product
    >>> second_asset.owner = customer
    >>> second_asset.save()

Create an Inventory::

    >>> Inventory = Model.get('stock.inventory')
    >>> InventoryLine = Model.get('stock.inventory.line')
    >>> Location = Model.get('stock.location')
    >>> storage, = Location.find([
    ...         ('code', '=', 'STO'),
    ...         ])
    >>> inventory = Inventory()
    >>> inventory.location = storage
    >>> inventory_line = inventory.lines.new()
    >>> inventory_line.product = product
    >>> inventory_line.quantity = 100.0
    >>> inventory_line.expected_quantity = 0.0
    >>> inventory_line = inventory.lines.new()
    >>> inventory_line.product = second_product
    >>> inventory_line.quantity = 100.0
    >>> inventory_line.expected_quantity = 0.0
    >>> inventory.click('confirm')
    >>> inventory.state
    u'done'


Configure Guarantee::

    >>> GuaranteeConfiguration = Model.get('guarantee.configuration')
    >>> guarantee_sequence, = Sequence.find([
    ...     ('code', '=', 'guarantee.guarantee'),
    ...     ], limit=1)
    >>> guarantee_config = GuaranteeConfiguration(1)
    >>> guarantee_config.guarantee_sequence = guarantee_sequence
    >>> guarantee_config.save()

Create a guarantee type that include services::

    >>> GuaranteeType = Model.get('guarantee.type')
    >>> guarantee_type = GuaranteeType(name='Services guarantee')
    >>> guarantee_type.includes_services = True
    >>> guarantee_type.duration = 12
    >>> guarantee_type.save()

Create a guarantee for the customer and the asset::

    >>> Guarantee = Model.get('guarantee.guarantee')
    >>> guarantee = Guarantee()
    >>> guarantee.party = customer
    >>> guarantee.document = asset
    >>> guarantee.type = guarantee_type
    >>> guarantee.start_date = today
    >>> guarantee.save()
    >>> guarantee.reload()
    >>> bool(guarantee.in_guarantee)
    True

Create a sale with a line in guarantee::

    >>> Sale = Model.get('sale.sale')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = service
    >>> sale_line.quantity = 10
    >>> sale_line.guarantee = guarantee
    >>> bool(sale_line.line_in_guarantee)
    True
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 10
    >>> sale_line.guarantee = guarantee
    >>> bool(sale_line.line_in_guarantee)
    False
    >>> sale.save()
    >>> guarantee_line, non_guarantee_line = sale.lines
    >>> guarantee_line.amount
    Decimal('0.00')
    >>> non_guarantee_line.amount
    Decimal('100.00')

Process the sale and check invoice lines are related to guarantee::

    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> invoice, = sale.invoices
    >>> invoice.untaxed_amount
    Decimal('100.00')
    >>> guarantee_line, non_guarantee_line = invoice.lines
    >>> guarantee_line.guarantee == guarantee
    True
    >>> bool(guarantee_line.line_in_guarantee)
    True
    >>> guarantee_line.amount
    Decimal('0.00')
    >>> guarantee_line.guarantee == guarantee
    True
    >>> bool(non_guarantee_line.line_in_guarantee)
    False
    >>> non_guarantee_line.amount
    Decimal('100.00')


Create a sale with guarnatee type and two products::

    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale.guarantee_type = guarantee_type
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.asset = second_asset
    >>> sale_line.quantity = 10
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = second_product
    >>> sale_line.asset = second_asset
    >>> sale_line.quantity = 10
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')

After partialy processing the shipment there is no guarantee::

    >>> shipment, = sale.shipments
    >>> for move in shipment.inventory_moves:
    ...     move.quantity = 5.0
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> guarantees = Guarantee.find([
    ...         ('document', '=', 'asset,' + str(second_asset.id)),
    ...         ])
    >>> len(guarantees)
    0

After fully sending the goods a new guarantee is created for the asset::

    >>> sale.reload()
    >>> _, shipment = sale.shipments
    >>> shipment.effective_date = tomorrow
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> guarantee, = Guarantee.find([
    ...         ('document', '=', 'asset,' + str(second_asset.id)),
    ...         ])
    >>> guarantee.type == guarantee_type
    True
    >>> guarantee.start_date == tomorrow
    True
    >>> guarantee.state
    u'draft'
    >>> guarantee.sale_lines == sale.lines
    True


Guarantee should not apply on sales until tomorrow::

    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = service
    >>> sale_line.quantity = 10
    >>> sale_line.asset = second_asset
    >>> sale_line.guarantee
    >>> bool(sale_line.line_in_guarantee)
    False
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.sale_date = tomorrow
    >>> sale.payment_term = payment_term
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = service
    >>> sale_line.quantity = 10
    >>> sale_line.asset = second_asset
    >>> sale_line.guarantee == guarantee
    True
    >>> bool(sale_line.line_in_guarantee)
    True
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 10
    >>> sale_line.asset = second_asset
    >>> sale_line.guarantee == guarantee
    True
    >>> bool(sale_line.line_in_guarantee)
    False

After processing the sale guarantees are linked to invoice lines::

    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> invoice, = sale.invoices
    >>> guarantee_line, non_guarantee_line = invoice.lines
    >>> guarantee_line.product == service
    True
    >>> guarantee_line.guarantee == guarantee
    True
    >>> guarantee_line.guarantee_asset == second_asset
    True
    >>> bool(guarantee_line.line_in_guarantee)
    True
    >>> non_guarantee_line.product == product
    True
    >>> non_guarantee_line.guarantee == guarantee
    True
    >>> bool(non_guarantee_line.line_in_guarantee)
    False


Guarantee should not apply on invoices until tomorrow::

    >>> Invoice = Model.get('account.invoice')
    >>> invoice = Invoice()
    >>> invoice.party = customer
    >>> invoice.payment_term = payment_term
    >>> invoice_line = invoice.lines.new()
    >>> invoice_line.product = service
    >>> invoice_line.quantity = 10
    >>> invoice_line.guarantee_asset = second_asset
    >>> invoice_line.guarantee
    >>> bool(invoice_line.line_in_guarantee)
    False
    >>> invoice = Invoice()
    >>> invoice.party = customer
    >>> invoice.invoice_date = tomorrow
    >>> invoice.payment_term = payment_term
    >>> invoice_line = invoice.lines.new()
    >>> invoice_line.product = service
    >>> invoice_line.quantity = 10
    >>> invoice_line.guarantee_asset = second_asset
    >>> invoice_line.guarantee == guarantee
    True
    >>> bool(invoice_line.line_in_guarantee)
    True
    >>> invoice_line = invoice.lines.new()
    >>> invoice_line.product = product
    >>> invoice_line.quantity = 10
    >>> invoice_line.guarantee_asset = second_asset
    >>> invoice_line.guarantee == guarantee
    True
    >>> bool(invoice_line.line_in_guarantee)
    False

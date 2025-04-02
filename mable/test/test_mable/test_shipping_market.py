from mable.shipping_market import AuctionMarket, TimeWindowTrade
from mable.transport_operation import Bid


class DummyShippingCompany:

    def __init__(self, name,  bid_amount):
        self.name = name
        self._bid_amount = bid_amount

    def inform(self, trades):
        bids = [Bid(amount=self._bid_amount, trade=one_trade) for one_trade in trades]
        return bids



class TestAuctionMarket:

    def test_distribute_trades(self):
        time = 0
        trades = [TimeWindowTrade(
            origin_port="A",
            destination_port="B",
            amount=1,
            cargo_type="Oil",
            time=0)]
        shipping_companies = [
            DummyShippingCompany("X", 1),
            DummyShippingCompany("Z", 3),
            DummyShippingCompany("Y", 2)]
        # noinspection PyTypeChecker
        # DummyShippingCompany is OK for the test no need to warn that it is no TradingCompany
        ledger = AuctionMarket.distribute_trades(time, trades, shipping_companies, timeout=60)
        sanitised_ledger = ledger.sanitised_ledger
        assert len(sanitised_ledger) == 3
        assert len(sanitised_ledger["X"]) == 1
        assert sanitised_ledger["X"][0].trade.origin_port == "A"
        assert sanitised_ledger["X"][0].trade.destination_port == "B"
        assert sanitised_ledger["X"][0].trade.amount == 1
        assert sanitised_ledger["X"][0].trade.cargo_type == "Oil"
        assert sanitised_ledger["X"][0].trade.time == 0
        assert sanitised_ledger["X"][0].payment == 2
        assert len(sanitised_ledger["Y"]) == 0
        assert len(sanitised_ledger["Z"]) == 0
        # Two companies
        # noinspection PyTypeChecker
        # DummyShippingCompany is OK for the test no need to warn that it is no TradingCompany
        ledger = AuctionMarket.distribute_trades(time, trades, shipping_companies[1:], timeout=60)
        sanitised_ledger = ledger.sanitised_ledger
        assert len(sanitised_ledger) == 2
        assert len(sanitised_ledger["Y"]) == 1
        assert sanitised_ledger["Y"][0].trade.origin_port == "A"
        assert sanitised_ledger["Y"][0].trade.destination_port == "B"
        assert sanitised_ledger["Y"][0].trade.amount == 1
        assert sanitised_ledger["Y"][0].trade.cargo_type == "Oil"
        assert sanitised_ledger["Y"][0].trade.time == 0
        assert sanitised_ledger["Y"][0].payment == 3
        assert len(sanitised_ledger["Z"]) == 0
        # One company
        # noinspection PyTypeChecker
        # DummyShippingCompany is OK for the test no need to warn that it is no TradingCompany
        ledger = AuctionMarket.distribute_trades(time, trades, shipping_companies[1:2], timeout=60)
        sanitised_ledger = ledger.sanitised_ledger
        assert len(sanitised_ledger) == 1
        assert len(sanitised_ledger["Z"]) == 1
        assert sanitised_ledger["Z"][0].trade.origin_port == "A"
        assert sanitised_ledger["Z"][0].trade.destination_port == "B"
        assert sanitised_ledger["Z"][0].trade.amount == 1
        assert sanitised_ledger["Z"][0].trade.cargo_type == "Oil"
        assert sanitised_ledger["Z"][0].trade.time == 0
        assert sanitised_ledger["Z"][0].payment == 3

    @staticmethod
    def assert_winner(sanitised_ledger, winner, others, payment):
        assert len(sanitised_ledger) == len(others) + 1
        for one_company in others:
            assert len(sanitised_ledger[one_company]) == 0
        assert len(sanitised_ledger[winner]) == 1
        assert sanitised_ledger[winner][0].payment == payment

    def test_distribute_trades_2(self, mocker):
        one_trade = TimeWindowTrade(
            origin_port="A",
            destination_port="B",
            amount=1,
            cargo_type="Oil",
            time=0)
        trades = [one_trade]
        shipping_company_1 = mocker.MagicMock()
        shipping_company_1.name = "1"
        shipping_company_2 = mocker.MagicMock()
        shipping_company_2.name = "2"
        shipping_company_3 = mocker.MagicMock()
        shipping_company_3.name = "3"
        shipping_company_4 = mocker.MagicMock()
        shipping_company_4.name = "4"
        # 1
        companies = [shipping_company_1, shipping_company_2, shipping_company_3, shipping_company_4]
        shipping_company_1.inform.return_value = [Bid(trade=one_trade, amount=5)]
        shipping_company_2.inform.return_value = [Bid(trade=one_trade, amount=10)]
        shipping_company_3.inform.return_value = [Bid(trade=one_trade, amount=15)]
        shipping_company_4.inform.return_value = [Bid(trade=one_trade, amount=20)]
        ledger = AuctionMarket.distribute_trades(0, trades, companies, timeout=60)
        self.assert_winner(ledger.sanitised_ledger, "1", ["2", "3", "4"], 10)
        # 2
        shipping_company_1.inform.return_value = [Bid(trade=one_trade, amount=50)]
        shipping_company_2.inform.return_value = [Bid(trade=one_trade, amount=10)]
        shipping_company_3.inform.return_value = [Bid(trade=one_trade, amount=20)]
        shipping_company_4.inform.return_value = [Bid(trade=one_trade, amount=15)]
        ledger = AuctionMarket.distribute_trades(0, trades, companies, timeout=60)
        self.assert_winner(ledger.sanitised_ledger, "2", ["1", "3", "4"], 15)
        # 3
        shipping_company_1.inform.return_value = [Bid(trade=one_trade, amount=19)]
        shipping_company_2.inform.return_value = [Bid(trade=one_trade, amount=50)]
        shipping_company_3.inform.return_value = [Bid(trade=one_trade, amount=15)]
        shipping_company_4.inform.return_value = [Bid(trade=one_trade, amount=20)]
        ledger = AuctionMarket.distribute_trades(0, trades, companies, timeout=60)
        self.assert_winner(ledger.sanitised_ledger, "3", ["1", "2", "4"], 19)
        # 4
        shipping_company_1.inform.return_value = [Bid(trade=one_trade, amount=50)]
        shipping_company_2.inform.return_value = [Bid(trade=one_trade, amount=20)]
        shipping_company_3.inform.return_value = [Bid(trade=one_trade, amount=17)]
        shipping_company_4.inform.return_value = [Bid(trade=one_trade, amount=15)]
        ledger = AuctionMarket.distribute_trades(0, trades, companies, timeout=60)
        self.assert_winner(ledger.sanitised_ledger, "4", ["1", "2", "3"], 17)

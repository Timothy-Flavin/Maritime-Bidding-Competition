from mable.cargo_bidding import TradingCompany
from mable.transport_operation import Bid

from loguru import logger

class Company8(TradingCompany):

    def pre_inform(self, trades, time):
        logger.warning("pre_inform")
        _ = self.propose_schedules(trades)

    def inform(self, trades, *args, **kwargs):
        """
        The shipping company that bids in cargo auctions.

        :param trades: The list of trades.
        :type trades: List[Trade]
        :param args: Not used.
        :param kwargs: Not used.
        :return: The bids of the company
        :rtype: List[Bid]
        """
        proposed_scheduling = self.propose_schedules(trades)
        scheduled_trades = proposed_scheduling.scheduled_trades
        trades_and_costs = [
            (x, proposed_scheduling.costs[x]) if x in proposed_scheduling.costs
            else (x, 0)
            for x in scheduled_trades]
        bids = [Bid(amount=cost, trade=one_trade) for one_trade, cost in trades_and_costs]
        return bids

    def receive(self, contracts, auction_ledger=None, *args, **kwargs):
        """
        Allocate a list of trades to the company.

        :param contracts: The list of trades.
        :type contracts: List[Contract]
        :param auction_ledger: Outcomes of all cargo auctions in the round.
        :type auction_ledger: AuctionLedger | None
        :param args: Not used.
        :param kwargs: Not used.
        """
        trades = [one_contract.trade for one_contract in contracts]
        scheduling_proposal = self.propose_schedules(trades)
        self.apply_schedules(scheduling_proposal.schedules)

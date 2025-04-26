from mable.cargo_bidding import TradingCompany
import random

class Company8(TradingCompany):
    def __init__(self, fleet, name="Group8"):
        super().__init__(fleet=fleet, name=name)
        self.random = random.Random(8)  # consistent randomness for debugging

    def pre_inform(self, date, upcoming_trades):
        self.future_trades = upcoming_trades

    def inform(self, date, trades):
        self.current_trades = trades

    def bid(self, date, trades):
        bids = {}

        for trade in trades:
            if self.random.random() < 0.2:  # 20% chance to bid
                bid_amount = self.random.randint(100, 1000)
                bids[trade.id] = bid_amount

        return bids

    def receive(self, date, won_trades):
        self.won_trades = won_trades

    def propose_schedules(self, date):
        schedules = {}

        for vessel in self._fleet:
            schedules[vessel.id] = vessel.schedule

        return schedules

from mable.cargo_bidding import TradingCompany

from loguru import logger

class Companyn(TradingCompany):

    def pre_inform(self, trades, time):
        logger.warning("pre_inform")
        _ = self.propose_schedules(trades)

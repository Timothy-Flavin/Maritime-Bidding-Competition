from mable.cargo_bidding import TradingCompany
from mable.transport_operation import Bid
from mable.transport_operation import ScheduleProposal

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

    def propose_schedules(self, trades):
        schedules = {}  # vessel -> schedule
        scheduled_trades = []
        costs = {}

        for vessel in self.fleet:  # for each ship
            schedules[vessel] = vessel.schedule.copy()  # start from current schedule

        for trade in trades:
            assigned = False
            for vessel in self.fleet:
                schedule = schedules[vessel].copy()  # copy so we can test safely
                try:
                    schedule.add_transportation(trade)  # try to just append
                    if schedule.verify_schedule():
                        schedules[vessel] = schedule  # commit
                        scheduled_trades.append(trade)
                        assigned = True
                        break  # done assigning this trade
                except Exception as e:
                    # Sometimes add_transportation can throw errors
                    pass

            if not assigned:
                # If no ship could take the trade, we just skip it
                pass
        
        self.calculate_cost(costs, trades)  # calculate costs for the trades

        return ScheduleProposal(schedules, scheduled_trades, costs)

    def calculate_cost(self, costs, trades):
        """
        Calculate the cost of the trade.

        :param costs: The costs of the trade.
        :type costs: Dict[Trade, float]
        :param trades: The trades.
        :type trades: List[Trade]
        """
        # inside propose_schedules
        for trade in trades:
            min_cost = float('inf')

            for ship in self.ships.values():
                # (1) Get the ship's current location
                ship_x, ship_y = ship.location
                
                # (2) Get the trade's pickup location
                pickup_x, pickup_y = trade.pickup_pos
                
                # (3) Get the trade's delivery location
                delivery_x, delivery_y = trade.delivery_pos
                
                # (4) Calculate distance to pickup
                dist_to_pickup = ((ship_x - pickup_x)**2 + (ship_y - pickup_y)**2) ** 0.5
                
                # (5) Calculate distance pickup to delivery
                dist_delivery = ((pickup_x - delivery_x)**2 + (pickup_y - delivery_y)**2) ** 0.5
                
                # (6) Total cost = distance to pickup + delivery distance
                total_cost = dist_to_pickup + dist_delivery
                
                if total_cost < min_cost:
                    min_cost = total_cost
            
            # (7) Set the bid cost for this trade as the minimal total cost among all ships
            costs[trade] = min_cost
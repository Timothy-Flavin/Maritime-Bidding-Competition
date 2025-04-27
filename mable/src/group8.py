import trade_utils  # Joe's work
import pickle  # For loading precomputed routes
from sa_scheduler import SAScheduler  # Tim's work
from mable.cargo_bidding import TradingCompany, Bid
from mable.transport_operation import ScheduleProposal, Schedule


class Group8Company(TradingCompany):
    def __init__(self, fleet, name):
        super().__init__(fleet, name)
        self._current_scheduling_proposal = None
        self._won_trades = []
        with open("precomputed_routes.pickle", "rb") as f:
            self.pr = pickle.load(f)
        self.simulated_annealing = SAScheduler(self)  # Initialize simulated annealing

    def inform(self, trades, *args, **kwargs):
        # Step 1: Generate initial feasible schedules
        schedules = trade_utils.generate_schedules_swapping(trades, num_schedules=10)

        # TODO - throw in Tim's simulated annealing here
        self.simulated_annealing.run(trades, self.pr, self.fleet)

        # Step 2: Pick the best schedule
        best_schedule_string = schedules[0]

        # Step 3: Build a schedule proposal
        self._current_scheduling_proposal = self.build_schedule_proposal(
            best_schedule_string, trades
        )

        # Step 4: Bid infinite for each scheduled trade
        bids = [
            Bid(amount=float("inf"), trade=trade)
            for trade in self._current_scheduling_proposal.scheduled_trades
        ]
        return bids

    def bid(self, date, trades):
        # Return an empty dict since bidding was handled in inform()
        return {}

    def receive(self, contracts, auction_ledger=None, *args, **kwargs):
        # Save the trades we actually won
        self._won_trades = [contract.trade for contract in contracts]

    def propose_schedules(self, date):
        # Propose the schedule built earlier
        if self._current_scheduling_proposal is None:
            raise ValueError(
                "No schedule proposal ready when propose_schedules() was called!"
            )
        return self._current_scheduling_proposal

    from mable.transport_operation import ScheduleProposal, Schedule


def build_schedule_proposal(self, schedule_string, trades):
    """
    Builds a ScheduleProposal based on a schedule string and trade list.

    Currently assigns everything to vessel 0 in order.
    """
    # Step 1: Create a new ScheduleProposal
    proposal = ScheduleProposal()

    # Step 2: Create a new blank Schedule for vessel 0
    vessel = self.vessels[0]  # You have a .vessels list from TradingCompany
    schedule = Schedule(vessel)

    # Step 3: Build a port -> trade lookup
    # We'll use the pickup port (uppercase) and dropoff port (lowercase) as keys
    trade_lookup = {}
    for trade in trades:
        pickup = trade.origin_port.name
        dropoff = trade.destination_port.name
        trade_lookup[pickup] = trade
        trade_lookup[dropoff] = trade

    # Step 4: Walk through the schedule string (like 'ABab')
    for port_char in schedule_string:
        port_name = port_char.upper() if port_char.isupper() else port_char.lower()

        if port_name not in trade_lookup:
            continue  # Safety check (shouldn't happen)

        trade = trade_lookup[port_name]

        if port_char.isupper():
            # Uppercase → pickup
            schedule.pickup(trade)
        else:
            # Lowercase → dropoff
            schedule.dropoff(trade)

    # Step 5: Add vessel's schedule to proposal
    proposal.add_schedule(schedule)

    return proposal

import trade_utils  # Joe's work
import pickle  # For loading precomputed routes
from sa_scheduler import SAScheduler  # Tim's work
from mable.cargo_bidding import TradingCompany, Bid
from mable.transport_operation import ScheduleProposal, Schedule
from mable.extensions.fuel_emissions import VesselWithEngine
from jank_logger import log, clear


class Group8Company(TradingCompany):
    def __init__(self, fleet, name):
        super().__init__(fleet, name)
        self._current_scheduling_proposal = None
        self._won_trades = []
        self.simulated_annealing = SAScheduler(self)  # Initialize simulated annealing
        clear()

    def inform(self, trades):
        """
        Called before each auction to inform the company of available trades.
        Runs Simulated Annealing to optimize our bids.
        """
        self.trades = trades

        # TODO: GET BETTER PRICES FOR BIDS
        bid_prices = []
        for trade in trades:
            bid_prices.append([])
            for vessel in self.fleet:
                bid_prices[-1].append(self.estimate_bid_price(trade, vessel))
        # Run Simulated Annealing to optimize schedule
        optimized_genome, optimized_cutoffs = self.simulated_annealing.run(
            trades, fleet=self.fleet, bid_prices=bid_prices, recieve=False
        )

        # Build a deterministic schedule from the optimized genome
        self._current_scheduling_proposal = (
            self.simulated_annealing.deterministic_schedule_from_genome(
                optimized_genome, optimized_cutoffs, self.fleet
            )
        )

        # Generate smart bids based on estimated travel cost + margin
        bids = []
        for trade in self._current_scheduling_proposal.scheduled_trades:
            assigned_vessel = self.pick_vessel_for_trade(trade)  # helper to get vessel
            bid_amount = self.estimate_bid_price(trade, assigned_vessel)
            bids.append(Bid(amount=bid_amount, trade=trade))
        return bids

    def pick_vessel_for_trade(self, trade):
        """
        Very simple placeholder: pick the vessel assigned to this trade.
        (You might eventually track real vessel assignments from SA output.)
        """
        # For now: pick first available vessel as a dumb default
        return self.fleet[0]
        # 🚨 TODO: Improve later by matching to vessels properly

    def bid(self, date, trades):
        # Return an empty dict since bidding was handled in inform()
        return {}

    def receive(self, won_trades, all_auction_outcomes):
        """
        Called after each auction to notify the company which trades it has won.
        Here we need to apply our proposed schedule for the won trades.
        """
        self.won_trades = won_trades  # Save for record-keeping

        if not won_trades:
            log("[Group8] No trades won this round.")
            return

        # Rebuild schedule from won trades only
        optimized_genome, optimized_cutoffs = self.simulated_annealing.run(
            won_trades, self.fleet
        )

        final_schedule_proposal = (
            self.simulated_annealing.deterministic_schedule_from_genome(
                optimized_genome, optimized_cutoffs, self.fleet
            )
        )

        if final_schedule_proposal is None:
            log(
                "[Group8] Warning: Failed to generate schedule! Submitting empty schedule."
            )
            final_schedule_proposal = self.generate_empty_schedule()

        # Submit schedule proposal to MABLE
        self.apply_schedules(final_schedule_proposal)

    def generate_empty_schedule(self):
        """
        Generate an empty ScheduleProposal (no operations).
        Useful as a fallback if no feasible schedule can be generated.
        """
        from mable.transport_operation import ScheduleProposal

        empty_proposal = ScheduleProposal()
        return empty_proposal

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

    def estimate_bid_price(self, trade, vessel: VesselWithEngine, profit_margin=0.10):
        """
        Estimate the cost for a vessel to complete a trade, and return a reasonable bid price.

        :param trade: Trade object (pickup port, dropoff port, etc.)
        :param pr: Port Route dictionary (paths and distances)
        :param vessel: Vessel object (capacity, speed, etc.)
        :param profit_margin: How much profit over cost (e.g., 0.10 = 10%)
        :return: Suggested bid amount (float)
        """
        pickup_port = trade.pickup_port
        dropoff_port = trade.dropoff_port
        vessel_port = (
            vessel.journey_log[-1].destination
            if vessel.journey_log
            else vessel.location
        )

        # Step 1: Calculate sailing distance to pickup
        try:
            to_pickup_distance = self.headquarters.get_network_distance(
                vessel_port, pickup_port
            )  # pr[vessel_port][pickup_port]["distance"]
        except KeyError:
            to_pickup_distance = 999999  # Big penalty if unreachable

        # Step 2: Calculate sailing distance from pickup to dropoff
        try:
            delivery_distance = self.headquarters.get_network_distance(
                pickup_port, dropoff_port
            )  # pr[pickup_port][dropoff_port]["distance"]
        except KeyError:
            delivery_distance = 999999  # Big penalty if unreachable

        total_distance = to_pickup_distance + delivery_distance

        # Step 3: Estimate sailing cost (simple linear cost model)
        cost_per_distance_unit = (
            1.0  # 🚨 TODO: tune this based on MABLE environment settings!
        )
        sailing_cost = total_distance * cost_per_distance_unit

        # Step 4: Add loading/unloading effort cost (optional)
        fixed_handling_cost = (
            100.0  # 🚨 TODO: tune this based on MABLE competition tuning!
        )
        total_cost = sailing_cost + fixed_handling_cost

        # Step 5: Add profit margin
        bid_price = total_cost * (1.0 + profit_margin)

        return bid_price

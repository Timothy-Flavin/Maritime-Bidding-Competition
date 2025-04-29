from mable.simulation_space.universe import OnJourney
import trade_utils  # Joe's work
import pickle  # For loading precomputed routes
from sa_scheduler import SAScheduler  # Tim's work
from mable.cargo_bidding import TradingCompany, Bid
from mable.transport_operation import ScheduleProposal, Schedule
from mable.extensions.fuel_emissions import VesselWithEngine
from jank_logger import log, clear
from mable.shipping_market import TimeWindowTrade
import config
import traceback


class Group8Company(TradingCompany):
    def __init__(self, fleet, name):
        super().__init__(fleet, name)
        self._current_scheduling_proposal = None
        self._won_trades = []
        log(f"[Group8] Initializing Group8Company with fleet: {fleet}")
        self.simulated_annealing = SAScheduler(self)  # Initialize simulated annealing
        clear()

    def inform(self, trades):
        """
        Called before each auction to inform the company of available trades.
        Runs Simulated Annealing to optimize our bids.
        """
        try:

            self.trades = trades
            log("Hello from Group8Company!")
            # TODO: GET BETTER PRICES FOR BIDS
            bid_prices = []
            for trade in trades:
                bid_prices.append([])
                for vessel in self.fleet:
                    try:
                        bid_prices[-1].append(
                            self.estimate_bid_price(trade, vessel, debug=True)
                        )
                    except Exception as e:
                        log(f"Error estimating bid price for trade {trade}: {e}")
                        log(traceback.format_exc())
                        exit()
            # Run Simulated Annealing to optimize schedule
            log(f"prices: {bid_prices}")
            try:
                optimized_genome, optimized_cutoffs = self.simulated_annealing.run(
                    trades,
                    fleet=self.fleet,
                    bid_prices=bid_prices,
                    recieve=False,
                    debug=False,
                )
            except Exception as e:
                log(f"Error running simulated annealing: {e}")
                log(traceback.format_exc())
                exit()
            log(f"optimized genome: {optimized_genome}")
            log(f"optimized cutoffs: {optimized_cutoffs}")
            # Build a deterministic schedule from the optimized genome
            schedules, tim_sched = (
                self.simulated_annealing.deterministic_schedule_from_genome(
                    optimized_genome, optimized_cutoffs, self.fleet
                )
            )
            log(f"optimized schedules: {schedules}")
            # Generate smart bids based on estimated travel cost + margin
            bids = []
            all_trades = []
            prop_dict = {}
            costs = {}
            for i, schedule in enumerate(schedules):
                # Get the vessel assigned to this schedule
                vessel = self.fleet[i]
                # Get the trades in this schedule
                log("trying to get trades")
                trades = schedule.get_scheduled_trades()
                log("hmm")
                # Add the trades to the list of all trades
                for t in trades:
                    all_trades.append(t)
                log("gonna add vessel to dict")
                prop_dict[vessel] = schedule
                log(f"vessel: {vessel}")
                log(f"trades: {trades}")
                # For each trade, estimate the bid price
                for trade in trades:
                    bid_amount = self.estimate_bid_price(trade, vessel)
                    bids.append(Bid(amount=bid_amount, trade=trade))
                    costs[trade] = bid_amount
            log(f"bids: {bids}")
            log(f"all trades: {all_trades}")
            log(f"prop_dict: {prop_dict}")
            self._current_scheduling_proposal = ScheduleProposal(
                schedules=prop_dict, scheduled_trades=all_trades, costs=costs
            )
            # for trade in self._current_scheduling_proposal.scheduled_trades:
            #     assigned_vessel = self.pick_vessel_for_trade(trade)  # helper to get vessel
            #     bid_amount = self.estimate_bid_price(trade, assigned_vessel)
            #     bids.append(Bid(amount=bid_amount, trade=trade))
        except Exception as e:
            log(f"ERROR IN INFORM SOMEHOW: {e}")
            log(traceback.format_exc())
            exit()
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

        final_schedule_proposal, tim_sched = (
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

        empty_proposal = ScheduleProposal()
        return empty_proposal

    def propose_schedules(self, date):
        # Propose the schedule built earlier
        if self._current_scheduling_proposal is None:
            raise ValueError(
                "No schedule proposal ready when propose_schedules() was called!"
            )
        return self._current_scheduling_proposal

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

    def estimate_bid_price(
        self,
        trade,
        vessel,
        expected_payment=None,
        profit_margin=0.1,
        debug=False,
    ):
        """
        Estimate travel cost for a trade and decide on a smart bid price.

        Args:
            trade: The Trade object.
            vessel: The Vessel object to assign the trade to.
            expected_payment: (Optional) How much we might be paid.
            debug: (Optional) Whether to log detailed info.

        Returns:
            - bid_price: float | None (None if we decide not to bid)
        """
        if debug:
            log("  Inside estimate_bid_price()")

        # Create a dummy schedule with just this trade

        sched = vessel.schedule.copy()
        sched.add_transportation(trade)
        # Estimate travel cost
        est_cost = self.simulated_annealing._est_travel_cost(vessel, sched, debug=debug)

        # Set a profit margin (20% recommended)
        profit_margin = 0.2

        bid_price = est_cost * (1 + profit_margin)

        # Optional: sanity check against expected payment if provided
        if expected_payment is not None:
            if bid_price > expected_payment:
                if debug:
                    print(
                        f"[BID SKIP] Estimated bid price {bid_price:.2f} > expected payment {expected_payment:.2f}."
                    )
                return None

        if debug:
            print(
                f"[BID] Trade {trade.origin_port.name} -> {trade.destination_port.name}"
            )
            print(f"    Est. cost: {est_cost:.2f}, Proposed bid: {bid_price:.2f}")

        return bid_price

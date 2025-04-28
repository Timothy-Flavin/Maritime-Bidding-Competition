# Simulated Annealing logic lives here
# (Tim imported these mostly for type hints)
from mable.transport_operation import Vessel, Trade
from mable.cargo_bidding import TradingCompany
from mable.extensions.fuel_emissions import VesselWithEngine
from mable.transportation_scheduling import Schedule
import random
import copy
from jank_logger import log, clear
from mable.simulation_space.universe import OnJourney
from mable.competition.information import CompanyHeadquarters
import numpy as np
import time


class SAScheduler:
    def __init__(
        self,
        company: TradingCompany,
        initial_temperature=2000,
        final_temperature=100,
        cooling_rate=0.98,
    ):
        self.company = company
        self.fleet = company.fleet
        # More initialization later
        self.starting_temperature = initial_temperature  # Initial temperature for SA
        self.final_temperature = final_temperature  # Final temperature for SA
        self.cooling_rate = cooling_rate  # Cooling rate for SA

    def generate_initial_genome(self, trades, bid_prices, debug=False):
        genome = []  # List of trades to be scheduled
        if debug:
            log(f"  Generating initial genome from {len(trades)} ")
            for trade in trades:
                log(f"    Trade: {trade}")
        min_time_window = self.company.headquarters.current_time
        max_time_window = min_time_window + 720  # 720 hours = 30 days

        print(f"  Min time window: {min_time_window}")
        print(f"  Max time window: {max_time_window}")
        for i, trade in enumerate(trades):
            tw = trade.time_window
            if tw[0] is None:
                tw[0] = min_time_window
            if tw[1] is None:
                tw[1] = max_time_window
            if tw[2] is None:
                tw[2] = min_time_window
            if tw[3] is None:
                tw[3] = max_time_window

            if debug:
                log(f"  Trade {i} Time window: {tw}")
            pickup = 10
            dropoff = 9
            while pickup >= dropoff:
                pickup = random.random() * (tw[1] - tw[0]) + tw[0]
                dropoff = random.random() * (tw[3] - tw[2]) + tw[2]

            genome.append(
                {
                    "trade": trade,
                    "trade_id": i,  # Unique ID for the trade
                    "tw": tw,
                    "current_pickup_allele": pickup,
                    "current_dropoff_allele": dropoff,
                    "active": False,  # Active trade in the genome
                    "prices": bid_prices[i],  # Prices for this trade for each vessel
                }
            )  # Store trade and its time windows
            if debug:
                log(
                    f"  Added trade {trade} with tw: {tw}, pickup at {pickup} and dropoff at {dropoff}"
                )
        if debug:
            log(f"  Initial genome: {genome}")
        cutoffs = []
        for i in range(len(self.fleet)):
            cutoffs.append(random.randint(0, len(genome) - 1))
        cutoffs.sort()  # Sort cutoffs to partition the genome
        if debug:
            log(f"  Cutoffs: {cutoffs}")
        random.shuffle(genome)  # Shuffle the genome to randomize trade order
        return genome, cutoffs  # To implement (maybe call a trade_utils function)

    def deterministic_schedule_from_genome(
        self, genome, cutoffs: list[int], fleet: list[VesselWithEngine], debug=False
    ):
        """
        Converts a genome into a legal and deterministic schedule for each vessel.
        The genome is a list of trades and cutoffs for each boat.
        """
        schedules = []  # List of schedules for each vessel
        simply_scheduled_trades = []  # List of trades scheduled for each vessel
        now = self.company.headquarters.current_time
        for i in range(len(genome)):
            genome[i]["active"] = False
        # Reset all trades to inactive before building the schedule
        if debug:
            print("Getting schedules from genome...")
            log(f"  Deterministic schedule with Cutoffs: {cutoffs}")
            log(f"  Fleet: {fleet}")
        for boat in fleet:
            schedules.append(boat.schedule.copy())  # Copy the initial schedule
            simple = schedules[
                -1
            ].get_simple_schedule()  # Ensure the schedule is initialized
            simply_scheduled_trades.append([])  # Initialize empty trade list

            # if existing schedule, convert it to a simple format
            for s in simple:
                simply_scheduled_trades[-1].append(
                    {
                        "gene": s[1],  # Trade object
                        "pickup": s[0] == "PICK_UP",  # True if pickup, False if dropoff
                        "time": now,  # set time to now to force new trades to be later
                    }
                )

        if debug:
            log(f"  Initial schedules: {schedules}")
            log(f"  Initial simply scheduled trades: {simply_scheduled_trades}")
        allele = 0  # Current allele index in the genome
        vessel_index = 0  # Index of the vessel we are currently scheduling trades for
        while allele < cutoffs[-1]:
            while allele >= cutoffs[vessel_index]:
                vessel_index += 1
            if vessel_index >= len(cutoffs):
                break
            if debug:
                log(f"    Scheduling trade {allele} for vessel {vessel_index}")
                log(
                    f"    Current schedule: {schedules[vessel_index].get_simple_schedule()}"
                )
            schedule_copy: Schedule = schedules[vessel_index].copy()
            # Go through events in this vessel's schedule and find the insertion points
            # for the current trade in the genome
            insertion_pickup = 0
            while (
                len(simply_scheduled_trades[vessel_index]) > 0  # check if exists yet
                and simply_scheduled_trades[vessel_index][insertion_pickup]["time"]
                < genome[allele]["current_pickup_allele"]
            ):
                insertion_pickup += 1
            if debug:
                log(f"    Insertion point for pickup: {insertion_pickup}")
            insertion_dropoff = insertion_pickup
            while (
                len(simply_scheduled_trades[vessel_index]) > 0
                and insertion_dropoff < len(simply_scheduled_trades[vessel_index])
                and simply_scheduled_trades[vessel_index][insertion_dropoff]["time"]
                < genome[allele]["current_dropoff_allele"]
            ):
                insertion_dropoff += 1

            if debug:
                log(f"    Insertion point for dropoff: {insertion_dropoff}")
            schedule_copy.add_transportation(
                genome[allele]["trade"],
                insertion_pickup + 1,  # 1 indexed
                insertion_dropoff + 1,
            )

            if debug:
                log(
                    f"    Checking schedule copy feasibility: {schedule_copy.get_simple_schedule()}\n    {schedule_copy.verify_schedule()}"
                )
            if schedule_copy.verify_schedule():
                schedules[vessel_index] = schedule_copy
                genome[allele][
                    "active"
                ] = True  # Mark this trade as active in the genome
                # Add the trade to the schedule and our simplified schedule list for sanity
                simply_scheduled_trades[vessel_index].insert(
                    insertion_dropoff,
                    {
                        "gene": genome[allele]["trade"],
                        "pickup": False,
                        "time": genome[allele]["current_dropoff_allele"],
                    },
                )  # Add trade to the vessel's scheduled trades
                simply_scheduled_trades[vessel_index].insert(
                    insertion_pickup,
                    {
                        "gene": genome[allele]["trade"],
                        "pickup": True,
                        "time": genome[allele]["current_pickup_allele"],
                    },
                )  # Add trade to the vessel's scheduled trades

                if debug:
                    log(
                        f"    Trade {allele} scheduled successfully on vessel {vessel_index}."
                    )
                    log(
                        f"    Feasable schedule: {simply_scheduled_trades[vessel_index]}"
                    )
            allele += 1  # Move to the next trade in the genome
        return schedules, simply_scheduled_trades

    def _est_travel_cost(
        self, vessel: VesselWithEngine, schedule: Schedule, debug=False
    ):
        if debug:
            log(f"Estimating travel cost for vessel {vessel.name}...")
        start_time = self.company.headquarters.current_time
        start_port = vessel.location
        if isinstance(start_port, OnJourney):
            start_port = start_port.destination
        if debug:
            log(f"  Start port: {start_port}")
            log(f"  Start time: {start_time}")
            log(f"  simple schedule: {schedule.get_simple_schedule()}")
        loading_costs, unloading_costs, travel_costs = 0, 0, 0
        loading_time, travel_time = 0, 0
        laden = 0
        for event in schedule.get_simple_schedule():
            if debug:
                log(f"    Event: {event}")
            dest_port = None
            if event[0] == "PICK_UP":
                # TODO: Handle idling before this pickup will not be trivial
                # Needs to be added to travel cost
                loading_time = vessel.get_loading_time(
                    event[1].cargo_type, event[1].amount
                )
                loading_costs += vessel.get_loading_consumption(loading_time)
                dest_port = event[1].origin_port
                laden += 1

            if event[0] == "DROP_OFF":
                loading_time = vessel.get_loading_time(
                    event[1].cargo_type, event[1].amount
                )
                unloading_costs += vessel.get_unloading_consumption(loading_time)
                dest_port = event[1].destination_port
                laden -= 1
            travel_distance = self.company.headquarters.get_network_distance(
                start_port, dest_port
            )  # TODO: deal with this being inf sometimes
            travel_time = vessel.get_travel_time(travel_distance)
            if laden > 0:
                travel_costs += vessel.get_laden_consumption(travel_time, vessel.speed)
            else:
                travel_costs += vessel.get_ballast_consumption(
                    travel_time, vessel.speed
                )

            if debug:
                log(
                    f"    Travel cost: {travel_costs}, Loading cost: {loading_costs}, Unloading cost: {unloading_costs}"
                )

        if debug:
            print(f"completion time: {schedule.completion_time()}")
        final_time = (
            schedule.completion_time()
            if len(schedule.get_simple_schedule()) > 0
            else start_time
        )
        idle_time = start_time + 720 - final_time
        # TODO: Check if 720 is right
        idle_cost = vessel.get_idle_consumption(idle_time)
        total_costs = loading_costs + unloading_costs + travel_costs + idle_cost

        if debug:
            log(f"  Total costs: {total_costs}")
            log(f"  Idle time: {idle_time}")
            log(f"  Idle cost: {idle_cost}")
            log(f"  Final time: {final_time}")
            log(f"  Start time: {start_time}")
        return total_costs

    def evaluate_fitness(self, schedules, genome, cutoffs, debug=False):
        # TODO: Add penalty for missing genome to fitness
        # Calculate expected income and travel costs if we get paid or not
        if debug:
            log(f"Evaluating fitness...")

        travel_cost = 0
        for vessel_index, schedule in enumerate(schedules):
            if debug:
                log(f"  Evaluating travel cost for vessel {vessel_index}... {schedule}")
            travel_cost += self._est_travel_cost(
                self.fleet[vessel_index], schedule, debug=debug
            )

        if debug:
            log(f"  summing active prices...")
        expected_income = 0
        cutoff_index = 0
        for g, gene in enumerate(genome):
            while g >= cutoffs[cutoff_index]:
                cutoff_index += 1
            if cutoff_index >= len(cutoffs):
                break
            if gene["active"]:
                if debug:
                    log(f"  Adding price for gene {g} with index {cutoff_index}")
                    log(f"  income: {gene["prices"][cutoff_index]}")
                expected_income += gene["prices"][cutoff_index]
        if debug:
            log(f"  Expected income: {expected_income}")
            log(f"  Travel cost: {travel_cost}")
            log(f"  Fitness: {expected_income - travel_cost}")
        return expected_income - travel_cost  # Fitness is income - cost

    def run(self, trades, bid_prices, fleet=None, recieve=False, debug=False):
        start = time.time()
        if fleet is not None:
            self.fleet = fleet

        if debug:
            log(f"Running Simulated Annealing with {len(trades)} trades.")
            log(f"Bid prices: {bid_prices}")
            log(f"Generating initial genome and cutoffs...")
        # 1. Generate an initial solution (genome + cutoffs)
        initial_genome, initial_cutoffs = self.generate_initial_genome(
            trades, bid_prices=bid_prices, debug=debug
        )
        initial_cutoffs[-1] = len(
            initial_genome
        )  # Ensure last cutoff includes all trades initially
        if debug:
            log(f"Initial genome: {initial_genome}")
            log(f"Initial cutoffs: {initial_cutoffs}")
            log(f"Getting schedules from genome...")

        schedules, simple_schedules = self.deterministic_schedule_from_genome(
            initial_genome, initial_cutoffs, self.fleet, debug=debug
        )
        current_genome = initial_genome
        current_cutoffs = initial_cutoffs

        if debug:
            log(
                f"Evaluating fitness of initial solution... from schedules: {schedules}"
            )
        current_fitness = self.evaluate_fitness(
            schedules=schedules,
            genome=current_genome,
            cutoffs=current_cutoffs,
            debug=debug,  # Pass debug flag to evaluate_fitness
        )
        if debug:
            log(f"Initial fitness: {current_fitness}")

        best_genome = current_genome
        best_cutoffs = current_cutoffs
        best_fitness = current_fitness

        temperature = self.starting_temperature
        iteration = 0
        # 2. Simulated Annealing Loop
        while temperature > self.final_temperature and time.time() - start < 10:
            # Mutation step
            if debug:
                log(f"Iteration {iteration}: Current fitness: {current_fitness}")
                log(f"Current temperature: {temperature}")
                log(f"Mutating solution...")
            mutated_genome, mutated_cutoffs = self.mutate_solution(
                current_genome, current_cutoffs, recieve=recieve, debug=debug
            )
            if debug:
                log(f"gettind determinstic schedule from mutated genome...")
            mutated_schedules, mutated_simple_schedules = (
                self.deterministic_schedule_from_genome(
                    mutated_genome, mutated_cutoffs, self.fleet, debug=debug
                )
            )
            # Fitness of mutated solution
            mutated_fitness = self.evaluate_fitness(
                schedules=mutated_schedules,
                genome=mutated_genome,
                cutoffs=mutated_cutoffs,
                debug=debug,
            )
            # Decide if we accept the new solution
            e = np.exp((mutated_fitness - current_fitness) / temperature)
            if debug:
                log(f"Mutated fitness: {mutated_fitness}")
                log(f"Current fitness: {current_fitness}")
                log(f"Acceptance probability: {e}")
            if mutated_fitness > current_fitness or random.random() < e:
                if debug:
                    log(f"Accepting mutated solution...")
                current_genome = mutated_genome
                current_cutoffs = mutated_cutoffs
                current_fitness = mutated_fitness

                if mutated_fitness > best_fitness:
                    best_genome = mutated_genome
                    best_cutoffs = mutated_cutoffs
                    best_fitness = mutated_fitness

            # Decrease temperature
            temperature *= self.cooling_rate
            iteration += 1

        # 3. Return best found solution
        return best_genome, best_cutoffs

    def mutate_solution(self, genome, cutoffs, recieve=False, debug=False):
        """
        Apply a small mutation to the genome and/or cutoffs.
        Returns a new mutated (genome, cutoffs).
        """
        # Deepcopy to avoid modifying in-place
        new_genome = copy.deepcopy(genome)
        new_cutoffs = copy.deepcopy(cutoffs)

        # Mutation options: swap two trades OR adjust cutoffs slightly
        mutation_type = random.choice(
            ["swap_trades", "adjust_cutoffs", "perturb_times"]
        )

        if mutation_type == "swap_trades":

            if len(new_genome) >= 2:
                i, j = random.sample(range(len(new_genome)), 2)
                if debug:
                    log(f"Swapping trades in genome... {i,j}")
                new_genome[i], new_genome[j] = new_genome[j], new_genome[i]

        elif mutation_type == "adjust_cutoffs":
            if len(new_cutoffs) > 0:
                idx = random.randint(0, len(new_cutoffs) - 1)
                adjustment = random.choice([-1, 1])
                new_cutoffs[idx] = max(0, new_cutoffs[idx] + adjustment)
                new_cutoffs = sorted(new_cutoffs)
            if recieve:
                new_cutoffs[-1] = len(genome)  # Ensure last cutoff includes all trades
            if debug:
                log(f"Adjusting cutoffs... {new_cutoffs}")
        elif mutation_type == "perturb_times":
            if len(new_genome) > 0:
                idx = random.randint(0, len(new_genome) - 1)
                gene = new_genome[idx]
                if debug:
                    log(
                        f"  Perturbing times for trade {idx} in genome... {gene['current_pickup_allele'], gene['current_dropoff_allele']}"
                    )
                gene["current_pickup_allele"] = 1
                gene["current_dropoff_allele"] = 0

                # If you store real-numbered timestamps in trade, you could slightly nudge them
                while gene["current_pickup_allele"] >= gene["current_dropoff_allele"]:
                    # Ensure pickup time is before dropoff time
                    # This is a simple perturbation, resample the pickup and dropoff times
                    # within the trade's time window
                    gene["current_pickup_allele"] = random.uniform(
                        gene["tw"][0], gene["tw"][1]
                    )
                    gene["current_dropoff_allele"] = random.uniform(
                        gene["tw"][2], gene["tw"][3]
                    )
                if debug:
                    log(
                        f"  To {gene['current_pickup_allele'], gene['current_dropoff_allele']}"
                    )
        return new_genome, new_cutoffs

from mable.cargo_bidding import TradingCompany
from mable.examples import environment, fleets
from mable.cargo_bidding import Bid
import math
import pandas as pd
import pickle
import random
from mable.transport_operation import Vessel, Trade, ScheduleProposal, Schedule
import time


class Simulated_Anealing:
    def __init__(
        self,
    ):
        pass

    def run(
        self,
        trades,
        paths,  # dict[port_name1+port_name2][0] = 'length', 'route'
        boats,  # List of boats
    ):
        start_time = time.time()
        print("Running Simulated Annealing...")
        ports, cutoffs, boatwise_ports, unused_ports = self.make_new_random_genome(
            trades, boats
        )
        trades_fulfilled, travel_cost, schedules = self.calculate_trades_fullfilled(
            boatwise_ports, trades, paths, boats
        )
        initial_fitness = self.fitness(
            trades_fulfilled, travel_cost, schedules, boats, paths
        )

        iteration = 0
        temperature = 1000  # Initial temperature for simulated annealing
        alpha = 0.99  # Cooling rate for temperature
        while time.time() - start_time < 40:  # Run for 40 seconds
            iteration += 1
            if temperature > 0.1:  # Stop if temperature is too low
                temperature *= alpha  # Decrease temperature

            new_ports, new_cutoffs, new_boatwise_ports, new_unused_ports = (
                self.mutate_genome(ports, cutoffs, boatwise_ports, unused_ports)
            )

            new_trades_fulfilled, new_travel_cost, new_schedules = (
                self.calculate_trades_fullfilled(
                    new_boatwise_ports, trades, paths, boats
                )
            )
            new_fitness = self.fitness(
                new_trades_fulfilled, new_travel_cost, new_schedules, boats, paths
            )

            # Simulated annealing update step TODO: Add temperature control
            if new_fitness > initial_fitness or random.random() < math.exp(
                (new_fitness - initial_fitness) / temperature
            ):
                # Accept the new genome
                ports = new_ports
                cutoffs = new_cutoffs
                boatwise_ports = new_boatwise_ports
                unused_ports = new_unused_ports
                trades_fulfilled = new_trades_fulfilled
                travel_cost = new_travel_cost
                schedules = new_schedules
                initial_fitness = new_fitness

    def make_new_random_genome(self, trades, boats: list[Vessel]):
        print("  Making new random genome...")
        ports = self.get_active_ports(trades)

        print("    Active ports: ", ports)
        cutoffs = []
        for cutoff in range(len(boats)):
            cutoffs.append(random.randint(0, len(ports) - 1))
        cutoffs.sort()  # sort the cutoffs so that we can use them to partition the genome
        # randomize the order of the ports
        random.shuffle(ports)  # randomize the order of the ports
        # Now we have a random genome, we need to partition the ports into the boats

        print(f"    Cutoffs: {cutoffs}")
        print(f"    Ports after shuffle: {ports}")

        boatwise_ports = []
        for boat in range(len(boats)):
            if boats[boat].location() == "OnJourney":
                boatwise_ports.append([])
                # If the boat is on a journey, we don't know where it is
                # we need to add it's destination port to the boatwise_ports
                continue  # TODO add desination port
            else:
                boatwise_ports.append([boats[boat].location()])  # Deal with OnJourney

        print(f"    Boatwise ports before partitioning: {boatwise_ports}")
        # now we partition the ports into the boats using the cutoffs
        cutoff_index = 0
        port_index = 0
        unused_ports = []
        # We will use the cutoffs to partition the ports into boatwise_ports
        while port_index < len(ports):
            if port_index >= cutoffs[-1]:
                unused_ports.append(ports[port_index])
                port_index += 1
                continue
            elif port_index <= cutoffs[cutoff_index]:
                boatwise_ports[cutoff_index].append(ports[port_index])
                port_index += 1
            else:
                cutoff_index += 1

        print(f"    Boatwise ports before partitioning: {boatwise_ports}")
        print(f"    Unused ports: {unused_ports}")
        return ports, cutoffs, boatwise_ports, unused_ports

    def get_active_ports(self, trades):
        ports = []
        for trade in trades:
            ports.append(trade.origin_port.name)
            ports.append(trade.destination_port.name)
        return ports

    # Given a set of genomes for the boats, boatwise ports, this function
    # calculates the trades that can be fulfilled legally by each boat
    # given this genome and it returns the resulting schedule for each boat
    def calculate_trades_fullfilled(
        self, boatwise_ports, trades, paths, boats: list[Vessel]
    ):
        print("  Calculating trades fulfilled...")
        # TODO: This is a bin packing problem so we want to find a better
        # way than what Tim Wrote below
        boatwise_trades = []  # List of trades fulfilled by each boat
        boatwise_cargo = []  # The cargo at each port
        schedules: list[Schedule] = []

        # assume we have no cargo
        for boat in range(len(boatwise_ports)):
            boatwise_cargo.append({})
            for cargo_type in boats[boat].cargo_types:
                boatwise_cargo[boat][cargo_type] = [0] * len(boatwise_ports[boat])
            schedules.append(boats[boat].schedule)

        for trade in trades:
            for boat in len(boatwise_ports):
                # Get index of trade origin poirt in boatwise_ports[boat]
                pickup_indices = [
                    i
                    for i, x in enumerate(boatwise_ports[boat])
                    if x == trade.origin_port.name
                ]  # gets all instances of pickup port in genome
                if len(pickup_indices) == 0:
                    continue
                else:
                    dropoff_indices = [
                        i
                        for i, x in enumerate(boatwise_ports[boat])
                        if x == trade.origin_port.name
                    ]  # gets all instances of dropoff port in genome
                    if len(dropoff_indices) == 0:
                        continue

                    cost = 1000000000  # Set a high cost to start with
                    for pi in pickup_indices:
                        for do in dropoff_indices:
                            # if the trade can be fulfilled by multiple segments
                            # choose the one with the lowest travel cost
                            est_cost, insertion1, insertion2 = self.check_trade_cost(
                                trade,
                                boats[boat],
                                boatwise_trades[boat],
                                pi,
                                do,
                            )
                            if est_cost < cost:
                                cost = est_cost
                                boatwise_trades[boat].append((pi, do))
                                sch: Schedule = schedules[boat]
                                sch.add_transportation(
                                    trade,
                                    insertion1,
                                    insertion2,
                                )
                                break  # go to next trade

    # Returns the increase in travel time and the insertion points
    # for a proposed trade in the boat's schedule
    def check_trade_cost(
        self,
        trade: Trade,
        boat: Vessel,
        boatwise_trades,
        pickup_ind: int,
        dropoff_ind: int,
        paths,
    ):
        if trade.cargo_type not in boat.loadable_cargo_types():
            return math.inf, 0, 0  # Cargo type not loadable by this boat

        sched_copy = boat.schedule.copy()
        # Add the trade to the schedule copy
        sched_copy.get_insertion_points()

        print("  Checking trade cost for:", trade)
        print("  Pickup index:", pickup_ind, "Dropoff index:", dropoff_ind)
        print(f"  schedule: {sched_copy}")
        print(f"  insertion points: {sched_copy.get_insertion_points()}")

        return True

    def fitness(self, trades_fulfilled, travel_cost, schedules, boats, paths):
        return (
            len(trades_fulfilled) / travel_cost * 1000
        )  # TODO: Implement fitness function


class Companyn(TradingCompany):
    def __init__(self, fleet, name):
        super().__init__(fleet, name)
        ports = pd.read_csv("ports.csv")
        # connections = pd.read_csv("time_transition_distribution.csv")

        with open("precomputed_routes.pickle", "rb") as f:
            pr = pickle.load(f)
        print(ports)
        # for p1 in ports["Port_Name"]:
        #    for p2 in ports["Port_Name"]:
        #        if p1 != p2:
        #            print(f"Distance from {p1} to {p2}: {pr[p1+p2][0].route}")
        #            input()
        # exit()

    def inform(self, trades, *args, **kwargs):
        print(f"Company {self._name} received trades: {trades}")
        schedule = Schedule(self.vessels[0])  # Just using the first vessel for now
        for trade in trades:
            print(trade)
            print(trade.origin_port.name, trade.destination_port)
            print(trade.amount, trade.cargo_type)
        exit()

        proposed_scheduling = self.propose_schedules(trades)
        scheduled_trades = proposed_scheduling.scheduled_trades
        self._current_scheduling_proposal = proposed_scheduling
        bids = [Bid(amount=math.inf, trade=one_trade) for one_trade in scheduled_trades]
        return bids

    def pre_inform(self, trades, time):
        print(f"Company {self._name} received trades: {trades} at time {time}")

    def receive(self, contracts, auction_ledger=None, *args, **kwargs):
        print(f"Company {self._name} received contracts: {contracts}")
        input("did that make sense?")


if __name__ == "__main__":
    specifications_builder = environment.get_specification_builder(
        environment_files_path="."
    )
    fleet = fleets.example_fleet_1()
    specifications_builder.add_company(
        Companyn.Data(Companyn, fleet, "My Shipping Corp Ltd.")
    )
    sim = environment.generate_simulation(specifications_builder)
    sim.run()

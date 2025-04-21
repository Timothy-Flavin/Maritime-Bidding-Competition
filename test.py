from mable.cargo_bidding import TradingCompany
from mable.examples import environment, fleets
from mable.cargo_bidding import Bid
import math
import pandas as pd
import pickle
import random
from mable.transport_operation import Vessel, Trade, ScheduleProposal, Schedule


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
        ports, cutoffs, boatwise_ports, unused_ports = self.make_new_random_genome(
            trades, boats
        )
        trades_fulfilled, travel_cost = self.calculate_trades_fullfilled(
            boatwise_ports, trades, paths
        )

    def make_new_random_genome(self, trades, boats: list[Vessel]):
        ports = self.get_active_ports(trades)
        cutoffs = []
        for cutoff in range(len(boats)):
            cutoffs.append(random.randint(0, len(ports) - 1))
        cutoffs.sort()  # sort the cutoffs so that we can use them to partition the genome
        # randomize the order of the ports
        random.shuffle(ports)

        boatwise_ports = []
        for boat in range(len(boats)):
            if boats[boat].location() == "OnJourney":
                boatwise_ports.append([])
                # If the boat is on a journey, we don't know where it is
                # we need to add it's destination port to the boatwise_ports
                continue  # TODO add desination port
            else:
                boatwise_ports.append([boats[boat].location()])  # Deal with OnJourney

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
        return ports, cutoffs, boatwise_ports, unused_ports

    def get_active_ports(self, trades):
        ports = []
        for trade in trades:
            ports.append(trade.origin_port.name)
            ports.append(trade.destination_port.name)
        return ports

    def calculate_trades_fullfilled(self, boatwise_ports, trades, paths, boats):
        # TODO: This is a knapsack problem so we want to find a better
        # way than what Tim Wrote below
        boatwise_trades = []  # List of trades fulfilled by each boat
        boatwise_cargo = []  # The cargo at each port

        # assume we have no cargo
        for boat in range(len(boatwise_ports)):
            boatwise_cargo.append({})
            for cargo_type in boats[boat].cargo_types:
                boatwise_cargo[boat][cargo_type] = [0] * len(boatwise_ports[boat])

        for trade in trades:
            for boat in len(boatwise_ports):
                schedule = Schedule(boats[boat])
                # Get index of trade origin poirt in boatwise_ports[boat]
                pickup_ind = boatwise_ports[boat].index(trade.origin_port.name)
                if pickup_ind == -1:
                    continue
                else:
                    dropoff_ind = boatwise_ports[boat].index(
                        trade.destination_port.name
                    )
                    if dropoff_ind == -1:
                        continue
                    elif dropoff_ind > pickup_ind:
                        self.check_trade_legality(
                            trade,
                            boatwise_cargo[boat],
                            boats[boat],
                            boatwise_ports[boat],
                            pickup_ind,
                            dropoff_ind,
                        )

    def check_trade_legality(
        self,
        trade: Trade,
        boat_cargo,
        boat: Vessel,
        boat_ports,
        pickup_ind,
        dropoff_ind,
        paths,
    ):
        if trade.cargo_type not in boat.loadable_cargo_types():
            return False

        capacity = boat.capacity(
            trade.cargo_type
        )  # Get the capacity of the boat for this cargo type
        capacity_used = 0
        time_at_port = 0  # Not used in this function, but could be useful later
        for p in range(len(boat_ports)):
            paths[boat_ports[p] + boat_ports[p + 1]][
                0
            ].length  # Get the time to get to the next port
            capacity_used += boat_cargo[trade.cargo_type][p]
            if p == pickup_ind:
                capacity_used += trade.amount
            if p == dropoff_ind:
                capacity_used -= trade.amount
            if capacity_used > capacity:
                return False
        # If we get here, the trade is legal
        return True

    def fitness(
        self,
        genome_port_list,  # List of port tuples port_name
        genome_partitions,
        all_trades,  # List of all trades
        paths,  # dict[port_name1+port_name2][0] = 'length', 'route'
        n_boats,
        starting_ports,
    ):
        genome_port_index = 0  # the item in the genome we are dealing with
        boat_num = 0
        # The port list is our full path, the item_list is the item destinations in this genome
        proposed_port_path = []
        proposed_port_path.append([starting_ports[0]])  # first boat start
        time_at_each_port = []
        time_at_each_port.append([0])  # first boat start

        # first we fix the genome by adding in free items that are already in the path
        # and we also
        while genome_port_index < len(genome_port_list):
            # if the item we are looking at is the partition number then we need to move
            # to the next boat's tasks because it is the first item in a next boat's inventory
            while (
                genome_port_index == genome_partitions[boat_num]
                and boat_num < n_boats - 1
            ):
                boat_num += 1
                proposed_port_path.append(
                    [starting_ports[boat_num]]
                )  # next boat start new path array
                time_at_each_port.append([0])  # start at time 0 for the next boat

            # Now we add the item to the boat's path and update the time at each port
            proposed_port_path[boat_num].append(genome_port_list[genome_port_index])
            time_at_each_port[boat_num].append(  # time to get to the first item
                float(
                    paths[
                        proposed_port_path[boat_num][-2]
                        + proposed_port_path[boat_num][-1]
                    ][0].length
                )
                + time_at_each_port[boat_num][-1]  # plus previous time.
                # Might change this away from cumulative time later
            )
            genome_port_index += 1

        # for boat in range(n_boats):
        #    calculate_items_per_boat(proposed_port_path[boat], time_at_each_port[boat])


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

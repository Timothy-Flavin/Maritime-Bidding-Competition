"""
trade_utils.py
Utility functions for generating, validating, and plotting maritime trade schedules.
"""

import random
import matplotlib.pyplot as plt

# ------------------------------------------------------------------------
# Generate fake trades with randomized pickup/dropoff time windows
# ------------------------------------------------------------------------
def generate_trades(num_trades, allow_nones=False):
    """
    Randomly generates a list of trade tuples with optional None time windows.
    
    Args:
        num_trades (int): Number of trades to generate.
        allow_nones (bool): Whether to allow None values for time windows.

    Returns:
        List of tuples [(pickup_port, dropoff_port, (ep, lp, ed, ld))]
    """

    def random_time_window(low, high):
        if low > high:
            return low  # or high (depending on your design), basically don't try random
        return random.randint(low, high)

    ports = [chr(65+i) for i in range(num_trades)]  # 'A', 'B', 'C', etc.
    dropoff_ports = [chr(97+i) for i in range(num_trades)]  # 'a', 'b', 'c', etc.

    trades = []
    for i in range(num_trades):
        ep = random_time_window(0, 5)
        lp = random_time_window(ep if ep is not None else 0, 20)
        ed = random_time_window(5 if lp is None else lp, 15)
        ld = random_time_window(ed if ed is not None else 15, 25)

        trades.append((ports[i], dropoff_ports[i], (ep, lp, ed, ld)))
    return trades

# ------------------------------------------------------------------------
# Replace None values in trades with valid earliest/latest integers
# ------------------------------------------------------------------------
def fix_trades(trades):
    """
    Replace None values in trades with minimum or maximum values based on all other times.
    Guarantees complete (integer-only) time windows.
    """
    times = [t for window in trades.values() for t in window if t is not None]
    min_time = min(times) - 1
    max_time = max(times) + 1
    fixed_trades = {}
    for port, (ep, lp, ed, ld) in trades.items():
        if ep is None: ep = min_time
        if ld is None: ld = max_time
        if ed is None: ed = ep
        if lp is None: lp = ld
        fixed_trades[port] = (ep, lp, ed, ld)
    return fixed_trades

# ------------------------------------------------------------------------
# Visualize trade time windows on a timeline
# ------------------------------------------------------------------------
def plot_schedule(trades):
    """Simple plot showing the pickup and dropoff windows for a set of trades."""
    _, ax = plt.subplots(figsize=(10, 5))
    
    for i, (_, _, (ep, lp, ed, ld)) in enumerate(trades):
        # Plot pickup window
        ax.plot([ep, lp], [i, i], 'g', label='Pickup Window' if i == 0 else "", linewidth=2)
        ax.scatter([ep, lp], [i, i], color='green')

        # Plot dropoff window
        ax.plot([ed, ld], [i, i], 'r', label='Dropoff Window' if i == 0 else "", linewidth=2)
        ax.scatter([ed, ld], [i, i], color='red')

    ax.set_yticks(range(len(trades)))
    ax.set_yticklabels([f"{pickup}->{dropoff}" for pickup, dropoff, _ in trades])
    ax.set_xlabel('Time')
    ax.set_title('Pickup and Dropoff Time Windows')
    ax.legend()
    plt.tight_layout()
    plt.savefig('schedule_plot.png')

# ------------------------------------------------------------------------
# Check if a schedule of pickups and dropoffs obeys the time windows
# ------------------------------------------------------------------------
def is_feasible(schedule, trades):
    """
    Check if a schedule is feasible based on time windows.
    Ports must occur respecting pickup before dropoff timing.
    """
    # Fix: convert trades into a quick lookup dictionary
    port_windows = {}
    for pickup, dropoff, (ep, lp, ed, ld) in trades:
        port_windows[pickup.upper()] = (ep, lp)
        port_windows[dropoff.lower()] = (ed, ld)

    current_time = 0
    cargo = set()

    for ch in schedule:
        if ch.upper() == ch:  # Pickup port
            ep, lp = port_windows[ch]
            if current_time > lp:
                return False  # Missed pickup window
            current_time = max(current_time, ep)
            cargo.add(ch)
        else:  # Dropoff port
            ed, ld = port_windows[ch]
            if ch.upper() not in cargo:
                return False  # Can't drop off what you haven't picked up
            if current_time > ld:
                return False  # Missed dropoff window
            current_time = max(current_time, ed)
            cargo.remove(ch.upper())

    return True

# ------------------------------------------------------------------------
# Generate initial simple schedules: earliest, midpoint, latest ordering
# ------------------------------------------------------------------------
def generate_init_schedules(trades):
    """
    Generate three basic schedules: earliest-based, midpoint-based, latest-based.
    """
    ports = {}
    for pickup, dropoff, (ep, lp, ed, ld) in trades:
        ports[pickup.upper()] = (ep, lp)
        ports[dropoff.upper()] = (ed, ld)

    earliest_order = sorted(ports.keys(), key=lambda x: ports[x][0])
    midpoint_order = sorted(ports.keys(), key=lambda x: (ports[x][0] + ports[x][1]) / 2)
    latest_order = sorted(ports.keys(), key=lambda x: ports[x][1])

    return [''.join(earliest_order), ''.join(midpoint_order), ''.join(latest_order)]

# ------------------------------------------------------------------------
# Create feasible schedules by random adjacent swaps
# ------------------------------------------------------------------------
def generate_schedules_swapping(trades, num_schedules=100):
    """
    Generate more feasible schedules by starting from simple schedules and randomly swapping adjacent ports.
    """
    schedules = generate_init_schedules(trades)
    while len(schedules) < num_schedules:
        schedule = list(random.choice(schedules))
        i = random.randint(0, len(schedule) - 2)
        schedule[i], schedule[i + 1] = schedule[i + 1], schedule[i]
        schedule = ''.join(schedule)
        if schedule not in schedules and is_feasible(schedule, trades):
            schedules.append(schedule)
    return schedules

# ------------------------------------------------------------------------
# Create feasible schedules by real-number sampling and sorting
# ------------------------------------------------------------------------
def generate_schedules_sampling(trades, num_schedules=100):
    """
    Generate feasible schedules by assigning random real numbers between windows and sorting by them.
    This guarantees feasibility without heavy checking.
    """
    schedules = []
    while len(schedules) < num_schedules:
        times = {}
        for port, (ep, lp, ed, ld) in trades.items():
            rp = random.uniform(ep, lp)
            rd = random.uniform(max(ed, rp), ld)
            times[port.upper()] = rp
            times[port.lower()] = rd
        ordered_ports = sorted(times.items(), key=lambda x: x[1])
        schedule = ''.join([p for p, _ in ordered_ports])
        if schedule not in schedules:
            schedules.append(schedule)
    return schedules

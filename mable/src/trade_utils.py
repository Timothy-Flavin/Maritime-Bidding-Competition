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
def is_feasible(sequence, trades):
    """
    Check whether a schedule sequence is feasible given trades.

    Args:
        sequence (str): A sequence of pickup/dropoff characters.
        trades (list or dict): Either a list of (pickup, dropoff, (ep, lp, ed, ld))
                               OR a dict {pickup_port: (ep, lp, ed, ld)}.

    Returns:
        bool: True if feasible, False otherwise.
    """
    # Preprocess trades into a dict no matter what
    if isinstance(trades, list):
        trade_dict = {pickup: (ep, lp, ed, ld) for pickup, dropoff, (ep, lp, ed, ld) in trades}
    elif isinstance(trades, dict):
        trade_dict = trades
    else:
        raise ValueError("trades must be a list or dictionary")

    time = 0
    visited = {}
    for ch in sequence:
        t = trade_dict[ch.upper()]  # Get time windows

        if ch.isupper():  # Pickup
            time = max(time, t[0])  # Earliest pickup
            if time > t[1]:  # Too late for pickup
                return False
            visited[ch.upper()] = time
        else:  # Dropoff
            if ch.upper() not in visited:
                return False  # Can't dropoff before pickup
            time = max(time, t[2])  # Earliest dropoff
            if time > t[3]:  # Too late for dropoff
                return False
    return True

# ------------------------------------------------------------------------
# Generate initial simple schedules: earliest, midpoint, latest ordering
# ------------------------------------------------------------------------
def generate_init_schedules(trades):
    """
    Generate initial schedules based on the time windows in trades.

    If trades is a dict, it should be of the format:
        { 'A': (ep, lp, ed, ld), ... }
    If trades is a list, it should be of the format:
        [('A', 'a', (ep, lp, ed, ld)), ...]

    Returns:
        A list of three schedule strings ordered by:
          1. Earliest time in the window
          2. Midpoint of the time window
          3. Latest time in the window
    """
    ports = {}
    if isinstance(trades, dict):
        # Convert the dict to a uniform mapping: key is uppercase letter (pickup)
        # and value is a tuple (ep, lp) for pickup, and for dropoff, use lowercase letter
        for port, windows in trades.items():
            ep, lp, ed, ld = windows
            ports[port.upper()] = (ep, lp)
            ports[port.lower()] = (ed, ld)
    elif isinstance(trades, list):
        # Each trade is a tuple: (pickup, dropoff, (ep, lp, ed, ld))
        for pickup, dropoff, windows in trades:
            ep, lp, ed, ld = windows
            ports[pickup] = (ep, lp)
            ports[dropoff] = (ed, ld)
    else:
        raise ValueError("trades must be either a dict or a list")

    # Order by earliest time in the time window for each port
    earliest_order = sorted(ports.keys(), key=lambda x: ports[x][0])
    # Order by midpoint of the time window
    midpoint_order = sorted(ports.keys(), key=lambda x: (ports[x][0] + ports[x][1]) / 2)
    # Order by latest time in the time window
    latest_order = sorted(ports.keys(), key=lambda x: ports[x][1])

    return [''.join(earliest_order), ''.join(midpoint_order), ''.join(latest_order)]

# ------------------------------------------------------------------------
# Create feasible schedules by random adjacent swaps
# ------------------------------------------------------------------------
def generate_schedules_sampling(trades, num_schedules=100):
    """
    Generate feasible schedules by sampling random times within the trade time windows.

    Args:
        trades (list or dict): List of (pickup, dropoff, (ep, lp, ed, ld)) or dict {pickup: (ep, lp, ed, ld)}.
        num_schedules (int): Number of schedules to generate.

    Returns:
        List of feasible schedule strings.
    """
    # Normalize trades into a ports dictionary: port -> (ep, lp)
    ports = {}
    if isinstance(trades, dict):
        for port, (ep, lp, ed, ld) in trades.items():
            ports[port.upper()] = (ep, lp)
            ports[port.lower()] = (ed, ld)
    elif isinstance(trades, list):
        for pickup, dropoff, (ep, lp, ed, ld) in trades:
            ports[pickup] = (ep, lp)
            ports[dropoff] = (ed, ld)
    else:
        raise ValueError("trades must be a list or dict")

    schedules = []
    while len(schedules) < num_schedules:
        times = {}
        for port, (ep, lp) in ports.items():
            rp = random.uniform(ep, lp)  # Random time within window
            times[port] = rp
        ordered_ports = sorted(times.items(), key=lambda x: x[1])
        schedule = ''.join([p for p, _ in ordered_ports])
        if schedule not in schedules:  # Keep unique schedules
            schedules.append(schedule)
    return schedules

# ------------------------------------------------------------------------
# Create feasible schedules by real-number sampling and sorting
# ------------------------------------------------------------------------
def generate_schedules_sampling(trades, num_schedules=100):
    """
    Generate feasible schedules by sampling random times within the trade time windows.

    Args:
        trades (list or dict): List of (pickup, dropoff, (ep, lp, ed, ld)) or dict {pickup: (ep, lp, ed, ld)}.
        num_schedules (int): Number of schedules to generate.

    Returns:
        List of feasible schedule strings.
    """
    # Normalize trades into a ports dictionary: port -> (ep, lp)
    ports = {}
    if isinstance(trades, dict):
        for port, (ep, lp, ed, ld) in trades.items():
            ports[port.upper()] = (ep, lp)
            ports[port.lower()] = (ed, ld)
    elif isinstance(trades, list):
        for pickup, dropoff, (ep, lp, ed, ld) in trades:
            ports[pickup] = (ep, lp)
            ports[dropoff] = (ed, ld)
    else:
        raise ValueError("trades must be either a list or dict")

    schedules = []
    while len(schedules) < num_schedules:
        times = {}
        for port, (ep, lp) in ports.items():
            rp = random.uniform(ep, lp)  # Random time within window
            times[port] = rp
        ordered_ports = sorted(times.items(), key=lambda x: x[1])
        schedule = ''.join([p for p, _ in ordered_ports])
        if schedule not in schedules:  # Keep unique schedules
            schedules.append(schedule)
    return schedules


# ------------------------------------------------------------------------
# Create feasible schedules by swapping adjacent ports
# ------------------------------------------------------------------------
def generate_schedules_swapping(trades, num_schedules=100):
    """
    Generate schedules by swapping adjacent ports from an initial schedule.

    Args:
        trades (list or dict): List of (pickup, dropoff, (ep, lp, ed, ld)) or dict.
        num_schedules (int): Number of schedules to generate.

    Returns:
        List of feasible schedule strings.
    """
    # Reuse the same normalization logic
    initial_schedules = generate_init_schedules(trades)
    schedules = list(initial_schedules)  # Start with the three initial schedules

    while len(schedules) < num_schedules:
        schedule = list(random.choice(schedules))  # Pick a random schedule
        if len(schedule) < 2:
            continue  # Not enough to swap
        i = random.randint(0, len(schedule) - 2)  # Pick random adjacent pair
        schedule[i], schedule[i + 1] = schedule[i + 1], schedule[i]  # Swap them
        new_schedule = ''.join(schedule)

        if new_schedule not in schedules:
            schedules.append(new_schedule)

    return schedules

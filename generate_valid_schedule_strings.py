import random

def generate_valid_sequences(trades):
    """
    trades: dict like {'A': (ep, lp, ed, ld), 'B': (...), ...}
    returns: list of valid strings (or sample randomly)
    """
    def is_feasible(sequence):
        # Check uppercase precedes lowercase, and time feasibility
        time = 0
        visited = {}
        for ch in sequence:
            t = trades[ch.upper()]
            if ch.isupper():
                time = max(time, t[0])  # Earliest pickup
                if time > t[1]: return False  # Too late for pickup
                visited[ch.upper()] = time
            else:
                if ch.upper() not in visited: return False  # Dropoff before pickup
                time = max(time, t[2])  # Earliest dropoff
                if time > t[3]: return False  # Too late
        return True

    from itertools import permutations
    base_letters = list(trades.keys())
    chars = base_letters + [ch.lower() for ch in base_letters]
    valid = []

    total_permutations = 0
    valid_permutations = 0
    for perm in permutations(chars):
        total_permutations += 1
        if all(perm.index(ch) < perm.index(ch.lower()) for ch in base_letters):
            if is_feasible(perm):
                valid.append(''.join(perm))
                valid_permutations += 1
    print(f"Fraction of valid permutations: {valid_permutations}/{total_permutations} {valid_permutations/total_permutations:.2%}")
    return valid

if __name__ == "__main__":
    trades = {
        'A': (1,2,9,10),
        'C': (3,4,6,7),
        'E': (2,5,10,13),
        'G': (1,8,9,16),
        # 'I': (6,7,20,21),
        'N': (5,10,15,20)
    }
    valid_sequences = generate_valid_sequences(trades)
    print("Valid sequences:", valid_sequences)

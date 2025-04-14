def shorest_path(adjacency_list: dict[str,dict[str,float]]) -> tuple[dict[str,dict[str,float], dict[str,dict[str,str]]]]:
    """Given the adjacency list of a graph, return the shortest path from each node to all other nodes.
    Also store the intermediate nodes in the path - i.e., from A to B, what's the first node to go to after A?

    Args:
        adjacency_list (dict[str,dict[str,float]]): distance between all nodes

    Returns:
        tuple[dict[str,dict[str,float], dict[str,dict[str,str]]]]: containing shortest path lengths and the shortest paths respectively
    """
    # Initialize the heap and the shortest path dictionary
    shortest_path = {}
    shortest_path_length = {}
    for node in adjacency_list:
        shortest_path[node] = {}
        shortest_path_length[node] = {}
        for target in adjacency_list:
            shortest_path[node][target] = None
            shortest_path_length[node][target] = float('inf')
        shortest_path[node][node] = node
        shortest_path_length[node][node] = 0
    for intermediate in adjacency_list:
        for source in adjacency_list:
            for target in adjacency_list:
                if source == target:
                    continue
                if intermediate == source or intermediate == target:
                    continue
                if adjacency_list[source][intermediate] + adjacency_list[intermediate][target] < shortest_path_length[source][target]:
                    shortest_path_length[source][target] = adjacency_list[source][intermediate] + adjacency_list[intermediate][target]
                    shortest_path[source][target] = intermediate

    return shortest_path, shortest_path_length
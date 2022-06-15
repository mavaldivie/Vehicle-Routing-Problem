
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def solve(distances: [[int]], deliveries: [int], pickups: [int], load_time: [int], capacities: [int]):
    """Stores the data for the problem."""
    oo = int(1e9)
    nodes = len(distances)
    vehicles = len(capacities)

    assert(nodes == len(deliveries))
    assert(nodes == len(pickups))
    assert(nodes == len(load_time))
    assert(vehicles == len(capacities))
    assert(deliveries[0] == 0)
    assert(pickups[0] == 0)
    assert(load_time[0] == 0)

    data = {}
    dist = [[oo for _ in range(2 * nodes - 1)] for _ in range(2 * nodes - 1)]
    for i in range(nodes):
        for j in range(nodes):
            u = i if i == 0 else 2 * i
            v = j if j == 0 else 2 * j - 1
            dist[u][v] = distances[i][j]
        if i != 0: dist[2 * i - 1][2 * i] = load_time[i]
    data['distance_matrix'] = dist
    data['num_vehicles'] = vehicles
    data['depot'] = 0
    data['vehicle_capacities'] = capacities
    data['deliveries'] = deliveries
    data['pickups'] = pickups
    data['load_time'] = load_time

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']), data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    def deliveries_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        if from_node % 2 == 1: return 0
        return data['deliveries'][(from_node + 1) // 2]
    deliveries_callback_index = routing.RegisterUnaryTransitCallback(deliveries_callback)
    routing.AddDimensionWithVehicleCapacity(
        deliveries_callback_index, 0, data['vehicle_capacities'], True, 'deliveries')

    def pickups_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        if from_node % 2 == 1: return 0
        return -data['pickups'][(from_node + 1) // 2] + data['deliveries'][from_node // 2]
    pickups_callback_index = routing.RegisterUnaryTransitCallback(pickups_callback)
    routing.AddDimensionWithVehicleCapacity(
        pickups_callback_index, 0, data['vehicle_capacities'], True, 'pickups')

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    dimension_name = 'Distance'
    routing.AddDimension(transit_callback_index, 0, oo, True, dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(1000)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(60)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)


    if solution: print_solution(data, manager, routing, solution)
    else: print('No solution found !')



def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    print(f'Objective: {solution.ObjectiveValue()}')
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            if node_index % 2 == 1:
                idx = (node_index + 1) // 2
                route_load += data['deliveries'][idx]
                plan_output += 'Node {0}: -{1}+{2} --> '\
                    .format(idx, data['deliveries'][idx], data['pickups'][idx])
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            arc = routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
            route_distance += arc
        plan_output += 'Node {0}: start {1})\n'.format(manager.IndexToNode(index), route_load)
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        plan_output += 'Load of the route: {}\n'.format(route_load)
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print('Total distance of all routes: {}m'.format(total_distance))
    print('Total load of all routes: {}'.format(total_load))




distances = [
    [0, 548, 776, 696, 582, 274, 502, 194, 308, 194, 536, 502, 388, 354, 468, 776, 662],
    [548, 0, 684, 308, 194, 502, 730, 354, 696, 742, 1084, 594, 480, 674, 1016, 868, 1210],
    [776, 684, 0, 992, 878, 502, 274, 810, 468, 742, 400, 1278, 1164, 1130, 788, 1552, 754],
    [696, 308, 992, 0, 114, 650, 878, 502, 844, 890, 1232, 514, 628, 822, 1164, 560, 1358],
    [582, 194, 878, 114, 0, 536, 764, 388, 730, 776, 1118, 400, 514, 708, 1050, 674, 1244],
    [274, 502, 502, 650, 536, 0, 228, 308, 194, 240, 582, 776, 662, 628, 514, 1050, 708],
    [502, 730, 274, 878, 764, 228, 0, 536, 194, 468, 354, 1004, 890, 856, 514, 1278, 480],
    [194, 354, 810, 502, 388, 308, 536, 0, 342, 388, 730, 468, 354, 320, 662, 742, 856],
    [308, 696, 468, 844, 730, 194, 194, 342, 0, 274, 388, 810, 696, 662, 320, 1084, 514],
    [194, 742, 742, 890, 776, 240, 468, 388, 274, 0, 342, 536, 422, 388, 274, 810, 468],
    [536, 1084, 400, 1232, 1118, 582, 354, 730, 388, 342, 0, 878, 764, 730, 388, 1152, 354],
    [502, 594, 1278, 514, 400, 776, 1004, 468, 810, 536, 878, 0, 114, 308, 650, 274, 844],
    [388, 480, 1164, 628, 514, 662, 890, 354, 696, 422, 764, 114, 0, 194, 536, 388, 730],
    [354, 674, 1130, 822, 708, 628, 856, 320, 662, 388, 730, 308, 194, 0, 342, 422, 536],
    [468, 1016, 788, 1164, 1050, 514, 514, 662, 320, 274, 388, 650, 536, 342, 0, 764, 194],
    [776, 868, 1552, 560, 674, 1050, 1278, 742, 1084, 810, 1152, 274, 388, 422, 764, 0, 798],
    [662, 1210, 754, 1358, 1244, 708, 480, 856, 514, 468, 354, 844, 730, 536, 194, 798, 0],
]
#in_demands = [0, 1, 1, 2, 4, 2, 4, 8, 8, 1, 2, 1, 2, 4, 4, 8, 8]
in_demands = [0, 1, 2, 3, 1, 1, 2, 1, 5, 1, 1, 1, 2, 1, 1, 4, 1]
out_demands = [0, 2, 1, 2, 2, 1, 4, 0, 1, 5, 2, 0, 1, 0, 2, 0, 2]
#out_demands = [0, 1, 3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
load_time= [0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
capacities = [3, 4, 5, 6]

solve(distances[:5][:5], in_demands[:5], out_demands[:5], load_time[:5], capacities)

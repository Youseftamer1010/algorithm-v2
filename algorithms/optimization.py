"""
Optimization Algorithms
A. Greedy: Traffic Signal Optimization
B. Dynamic Programming: Bus/Metro Schedule Optimization
C. Dynamic Programming: Road Maintenance Resource Allocation
D. Greedy Optimality Analysis
E. Resource Allocation (Emergency Vehicles)

Complexity Summary:
- Traffic Signal Greedy:  O(V * degree) time, O(V) space
- Bus Schedule DP:       O(S * B^2) time, O(S * B) space  [S=stops, B=buses]
- Road Maintenance DP:   O(E * W) time, O(E * W) space    [E=edges, W=budget]
- Greedy Analysis:       O(n * k!) time for brute-force comparison
- Emergency Allocation:  O(incidents * depots * (V+E)logV) time
"""

from functools import lru_cache
from typing import List, Dict, Tuple, Optional
from data.graph_model import TransportGraph, Node


# ─── A. Greedy Traffic Signal Optimization ────────────────────────────────────

class TrafficSignal:
    def __init__(self, node_id: int, name: str, num_phases: int):
        self.node_id = node_id
        self.name = name
        self.num_phases = num_phases
        self.green_times: List[int] = [30] * num_phases  # seconds per phase
        self.total_cycle = sum(self.green_times)

    def optimize(self, incoming_flows: List[float], emergency: bool = False):
        """
        Greedy optimization: allocate green time proportional to traffic flow.
        Emergency mode: give maximum green to emergency direction.
        """
        total_flow = sum(incoming_flows) or 1.0

        if emergency:
            # Give 70% to emergency direction, split rest
            max_idx = incoming_flows.index(max(incoming_flows))
            self.green_times = [15] * self.num_phases
            self.green_times[max_idx] = 90
        else:
            cycle = 120  # 2-minute cycle
            self.green_times = [
                max(15, int((flow / total_flow) * cycle))
                for flow in incoming_flows
            ]
        self.total_cycle = sum(self.green_times)

    @property
    def efficiency_score(self) -> float:
        """Higher = more evenly distributed, less waiting"""
        if not self.green_times:
            return 0.0
        avg = self.total_cycle / len(self.green_times)
        variance = sum((t - avg)**2 for t in self.green_times) / len(self.green_times)
        return max(0, 100 - variance / 10)


def optimize_all_signals(graph: TransportGraph, time_index: int = 0) -> Dict[int, TrafficSignal]:
    """
    Greedy traffic signal optimization for all intersection nodes.
    Returns dict of node_id -> TrafficSignal
    """
    from data.cairo_data import TRAFFIC_PATTERNS

    signals = {}

    for node_id, node in graph.nodes.items():
        neighbors = graph.get_neighbors(node_id)
        if len(neighbors) < 2:
            continue  # Not an intersection

        num_phases = min(len(neighbors), 4)
        signal = TrafficSignal(node_id, node.name, num_phases)

        # Estimate incoming flow per direction
        incoming_flows = []
        for (_, edge) in neighbors[:num_phases]:
            mult = TRAFFIC_PATTERNS.get(edge.road_type, [1.0]*4)[time_index]
            flow = edge.capacity * mult * 0.4  # 40% baseline utilization
            incoming_flows.append(flow)

        signal.optimize(incoming_flows)
        signals[node_id] = signal

    return signals


def emergency_signal_priority(graph: TransportGraph, path_nodes: List[int],
                              signals: Dict[int, TrafficSignal]) -> Dict[int, TrafficSignal]:
    """
    Greedy: preempt traffic signals along emergency route.
    Give maximum green to emergency vehicle direction at each intersection.
    """
    updated = {}
    for i, node_id in enumerate(path_nodes[:-1]):
        if node_id in signals:
            sig = signals[node_id]
            next_node = path_nodes[i + 1]
            neighbors = graph.get_neighbors(node_id)
            neighbor_ids = [n for (n, _) in neighbors]
            if next_node in neighbor_ids:
                idx = neighbor_ids.index(next_node)
                flows = [0.0] * sig.num_phases
                if idx < len(flows):
                    flows[idx] = 1000.0  # max priority
                sig.optimize(flows, emergency=True)
            updated[node_id] = sig
    return updated


# ─── B. Dynamic Programming: Bus Schedule ─────────────────────────────────────

def optimize_bus_schedule(route_nodes: List[int], graph: TransportGraph,
                          time_index: int = 0, num_buses: int = 5,
                          demand_per_stop: List[float] = None) -> dict:
    """
    DP optimization for bus headways (frequency) to minimize passenger wait time
    subject to bus fleet size constraint.

    DP State: (stop_index, buses_remaining)
    DP Value: minimum total passenger-minutes of waiting

    At each stop i, we decide how many buses b_i to allocate to the segment
    from stop i to stop i+1. The headway on that segment is:
        headway_i = travel_time_i / b_i
    and the passenger wait cost is:
        cost_i = demand_i * headway_i / 2   (average wait = headway/2)

    Transition:
        dp(i, remaining) = min over b in [1..remaining-(n-i-1)+1] of
            demand_i * (travel_time_i / b) / 2 + dp(i+1, remaining - b)

    Base case:
        dp(n-1, remaining) = 0   (last stop has no outgoing segment)

    Time Complexity:  O(S * B^2) where S = stops, B = buses
    Space Complexity: O(S * B) for the memoization table

    Args:
        route_nodes: ordered list of stop IDs
        graph: TransportGraph
        time_index: traffic period (0-3)
        num_buses: total buses available for this route
        demand_per_stop: passengers/hour at each stop (default: use population proxy)

    Returns:
        dict with optimal_config, schedule, allocation, savings
    """
    n = len(route_nodes)
    if n < 2:
        return {"error": "Need at least 2 stops"}

    # Default demand based on node population
    if demand_per_stop is None:
        demand_per_stop = []
        for nid in route_nodes:
            node = graph.get_node(nid)
            pop = node.population if node else 100000
            importance = node.importance if node else 5
            demand_per_stop.append(max(50, pop / 1000 * importance / 5))

    # Travel times between consecutive stops
    travel_times = []
    for i in range(n - 1):
        edge = graph.get_edge(route_nodes[i], route_nodes[i + 1])
        if edge:
            t = edge.effective_weight(time_index, "bus")
        else:
            t = 15.0  # default 15 min if no direct edge
        travel_times.append(t)

    total_route_time = sum(travel_times)

    # ── DP Table ──
    # dp[i][b] = minimum total wait cost from stop i onward with b buses remaining
    # We use -1 to represent uncomputed states (infinity)
    INF = float('inf')
    dp = [[INF] * (num_buses + 1) for _ in range(n)]
    choice = [[0] * (num_buses + 1) for _ in range(n)]  # track optimal bus allocation

    # Base case: last stop, no outgoing segment, cost = 0 regardless of remaining buses
    for b in range(num_buses + 1):
        dp[n - 1][b] = 0.0

    # Fill DP table from stop n-2 down to stop 0
    for i in range(n - 2, -1, -1):
        for b in range(1, num_buses + 1):
            # Minimum buses needed for remaining segments: at least 1 per segment
            min_for_rest = max(0, (n - 1) - i - 1)  # segments after this one
            max_alloc_here = b - min_for_rest  # can't allocate more than this

            if max_alloc_here < 1:
                # Not enough buses to cover remaining segments; skip
                continue

            for alloc in range(1, max_alloc_here + 1):
                # Headway on segment i = travel_time / alloc
                headway = travel_times[i] / alloc
                # Wait cost at stop i = demand * average_wait = demand * headway / 2
                cost_here = demand_per_stop[i] * headway / 2.0
                cost_rest = dp[i + 1][b - alloc]
                total_cost = cost_here + cost_rest

                if total_cost < dp[i][b]:
                    dp[i][b] = total_cost
                    choice[i][b] = alloc

    # If DP couldn't find a valid solution (not enough buses for all segments),
    # fall back to uniform allocation
    if dp[0][num_buses] == INF:
        headway = total_route_time / num_buses
        optimal_wait = sum(d * headway / 2 for d in demand_per_stop[:-1])
        allocation = []
        for i in range(n - 1):
            allocation.append({
                "segment": f"Stop {i} → Stop {i+1}",
                "buses_allocated": 1,
                "headway_min": round(headway, 1),
                "travel_time_min": round(travel_times[i], 1),
                "demand": round(demand_per_stop[i], 1),
                "wait_cost": round(demand_per_stop[i] * headway / 2.0, 1),
            })
    else:
        # Backtrack to find optimal allocation per segment
        optimal_wait = dp[0][num_buses]
        allocation = []
        remaining = num_buses
        for i in range(n - 1):
            alloc = choice[i][remaining]
            if alloc <= 0:
                alloc = 1  # safety fallback
            headway = travel_times[i] / alloc
            allocation.append({
                "segment": f"Stop {i} → Stop {i+1}",
                "buses_allocated": alloc,
                "headway_min": round(headway, 1),
                "travel_time_min": round(travel_times[i], 1),
                "demand": round(demand_per_stop[i], 1),
                "wait_cost": round(demand_per_stop[i] * headway / 2.0, 1),
            })
            remaining -= alloc

    # Compute overall headway (weighted average)
    total_demand = sum(demand_per_stop[:-1])  # exclude last stop (no outgoing)
    avg_headway = optimal_wait / (total_demand / 2) if total_demand > 0 else 0

    # Build timetable for first bus
    schedule = []
    t = 0.0
    for i, nid in enumerate(route_nodes):
        node = graph.get_node(nid)
        schedule.append({
            "stop": node.name if node else f"Stop {nid}",
            "arrival_min": round(t, 1),
            "demand": round(demand_per_stop[i], 0),
        })
        if i < len(travel_times):
            t += travel_times[i]

    # Savings vs no optimization (30-min avg wait baseline, uniform 1 bus per segment)
    baseline_wait = sum(d * 30 for d in demand_per_stop[:-1])
    savings_pct = max(0, (baseline_wait - optimal_wait) / max(baseline_wait, 1) * 100)

    # Best config summary
    best_config = {
        "buses": num_buses,
        "headway_min": round(avg_headway, 1),
        "total_route_time": round(total_route_time, 1),
        "total_wait": round(optimal_wait, 1),
    }

    return {
        "optimal_config": best_config,
        "schedule": schedule,
        "allocation": allocation,
        "travel_times": travel_times,
        "demand": demand_per_stop,
        "savings_percent": round(savings_pct, 1),
        "optimized_wait": round(optimal_wait, 1),
        "baseline_wait": round(baseline_wait, 1),
    }


# ─── C. Dynamic Programming: Road Maintenance Resource Allocation ─────────────

def optimize_road_maintenance(graph: TransportGraph, budget_m_egp: float,
                               time_index: int = 0) -> dict:
    """
    DP solution for road maintenance resource allocation.
    Given a fixed budget, select which roads to repair to maximize
    network efficiency improvement. This is a 0/1 Knapsack-style DP.

    DP State: dp[edge_index][budget_remaining] = max achievable benefit
    DP Transition:
        dp[i][w] = max(
            dp[i-1][w],                          # skip this road
            dp[i-1][w - cost_i] + benefit_i      # repair this road
        ) if cost_i <= w else dp[i-1][w]

    Benefit of repairing a road = (condition_improvement) * (traffic_volume)
        - condition_improvement = 10 - current_condition  (repair brings to 10)
        - traffic_volume = capacity * traffic_multiplier (at given time)

    Time Complexity:  O(E * W) where E = edges, W = budget (discretized)
    Space Complexity: O(E * W) for the DP table

    Args:
        graph: TransportGraph
        budget_m_egp: total budget in million EGP
        time_index: traffic period for benefit calculation

    Returns:
        dict with selected roads, total cost, total benefit, efficiency gain
    """
    from data.cairo_data import TRAFFIC_PATTERNS

    # Only consider existing roads with condition < 8 (repairable)
    repairable = [e for e in graph.existing_edges() if e.condition < 8]

    if not repairable:
        return {
            "selected_roads": [],
            "total_cost": 0,
            "total_benefit": 0,
            "budget": budget_m_egp,
            "efficiency_gain_pct": 0,
            "message": "No repairable roads found"
        }

    # Discretize budget to integer units (1 unit = 1M EGP)
    W = int(budget_m_egp)
    n = len(repairable)

    # Compute benefit and cost for each road
    benefits = []
    costs = []
    for edge in repairable:
        condition_improvement = 10.0 - edge.condition
        mult = TRAFFIC_PATTERNS.get(edge.road_type, [1.0]*4)[time_index]
        traffic_volume = edge.capacity * mult * 0.4
        benefit = condition_improvement * traffic_volume * edge.distance
        cost = int(edge.cost)  # cost in M EGP, discretized

        benefits.append(benefit)
        costs.append(cost)

    # DP table: dp[i][w] = max benefit using first i roads with budget w
    dp = [[0.0] * (W + 1) for _ in range(n + 1)]

    # Fill DP table
    for i in range(1, n + 1):
        for w in range(W + 1):
            # Option 1: skip road i-1
            dp[i][w] = dp[i - 1][w]
            # Option 2: repair road i-1 (if it fits in budget)
            if costs[i - 1] <= w:
                candidate = dp[i - 1][w - costs[i - 1]] + benefits[i - 1]
                if candidate > dp[i][w]:
                    dp[i][w] = candidate

    # Backtrack to find which roads were selected
    selected = []
    w = W
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            # Road i-1 was selected
            edge = repairable[i - 1]
            node_u = graph.get_node(edge.u)
            node_v = graph.get_node(edge.v)
            selected.append({
                "road": f"{node_u.name if node_u else edge.u} ↔ {node_v.name if node_v else edge.v}",
                "current_condition": edge.condition,
                "improved_condition": 10.0,
                "cost_m_egp": edge.cost,
                "benefit": round(benefits[i - 1], 1),
                "road_type": edge.road_type,
                "distance_km": edge.distance,
            })
            w -= costs[i - 1]

    total_cost = sum(s["cost_m_egp"] for s in selected)
    total_benefit = dp[n][W]

    # Compute baseline network inefficiency (sum of condition deficits * traffic)
    baseline_inefficiency = sum(benefits)  # if all repairable roads were fixed
    efficiency_gain = (total_benefit / max(baseline_inefficiency, 1)) * 100

    return {
        "selected_roads": selected,
        "total_cost": round(total_cost, 1),
        "total_benefit": round(total_benefit, 1),
        "budget": budget_m_egp,
        "budget_used": round(budget_m_egp - w, 1),
        "efficiency_gain_pct": round(efficiency_gain, 1),
        "roads_repaired": len(selected),
        "roads_considered": n,
    }


# ─── D. Greedy Optimality Analysis ────────────────────────────────────────────

def analyze_greedy_performance(graph: TransportGraph, time_index: int = 0) -> dict:
    """
    Analyze cases where greedy traffic signal optimization is optimal vs suboptimal.

    Greedy approach: allocate green time proportional to incoming traffic flow.
    Optimal approach: enumerate all possible green-time splits (brute-force for
    small intersections) and find the one minimizing total wait time.

    For an intersection with k phases and cycle C, total wait is:
        sum_i (flow_i * (C - green_i))   [wait = red time * flow]

    Greedy minimizes variance of green times proportional to flow, which is
    optimal when flows are uniform but suboptimal when flows are highly
    asymmetric (a few dominant directions starve minor directions).

    Time Complexity: O(n * k! * C) for brute-force enumeration per intersection
    Space Complexity: O(k) per intersection

    Args:
        graph: TransportGraph
        time_index: traffic period

    Returns:
        dict with optimal_cases, suboptimal_cases, analysis summary
    """
    from data.cairo_data import TRAFFIC_PATTERNS
    from itertools import product

    signals = optimize_all_signals(graph, time_index)
    optimal_cases = []
    suboptimal_cases = []

    for node_id, signal in signals.items():
        if signal.num_phases < 2:
            continue

        # Get incoming flows for this intersection
        neighbors = graph.get_neighbors(node_id)
        num_phases = min(len(neighbors), signal.num_phases)
        incoming_flows = []
        for (_, edge) in neighbors[:num_phases]:
            mult = TRAFFIC_PATTERNS.get(edge.road_type, [1.0]*4)[time_index]
            flow = edge.capacity * mult * 0.4
            incoming_flows.append(flow)

        if not incoming_flows:
            continue

        # ── Greedy solution ──
        cycle = 120
        total_flow = sum(incoming_flows) or 1.0
        greedy_greens = [max(15, int((f / total_flow) * cycle)) for f in incoming_flows]
        # Normalize to exactly cycle length
        diff = cycle - sum(greedy_greens)
        if diff != 0 and greedy_greens:
            greedy_greens[0] += diff
        greedy_wait = sum(f * (cycle - g) for f, g in zip(incoming_flows, greedy_greens))

        # ── Optimal solution (brute-force over discretized green times) ──
        # Search over all valid green-time splits where sum = cycle, each >= 15
        best_wait = float('inf')
        best_greens = greedy_greens[:]

        # For small phase counts (2-4), enumerate feasible splits in steps of 5
        step = 5
        min_green = 15
        if num_phases == 2:
            for g1 in range(min_green, cycle - min_green + 1, step):
                g2 = cycle - g1
                if g2 < min_green:
                    continue
                wait = incoming_flows[0] * (cycle - g1) + incoming_flows[1] * (cycle - g2)
                if wait < best_wait:
                    best_wait = wait
                    best_greens = [g1, g2]
        elif num_phases == 3:
            for g1 in range(min_green, cycle - 2*min_green + 1, step):
                for g2 in range(min_green, cycle - g1 - min_green + 1, step):
                    g3 = cycle - g1 - g2
                    if g3 < min_green:
                        continue
                    wait = sum(f * (cycle - g) for f, g in
                              zip(incoming_flows, [g1, g2, g3]))
                    if wait < best_wait:
                        best_wait = wait
                        best_greens = [g1, g2, g3]
        elif num_phases == 4:
            for g1 in range(min_green, cycle - 3*min_green + 1, step):
                for g2 in range(min_green, cycle - g1 - 2*min_green + 1, step):
                    for g3 in range(min_green, cycle - g1 - g2 - min_green + 1, step):
                        g4 = cycle - g1 - g2 - g3
                        if g4 < min_green:
                            continue
                        wait = sum(f * (cycle - g) for f, g in
                                  zip(incoming_flows, [g1, g2, g3, g4]))
                        if wait < best_wait:
                            best_wait = wait
                            best_greens = [g1, g2, g3, g4]
        else:
            # For higher phase counts, greedy is used as approximation
            best_wait = greedy_wait
            best_greens = greedy_greens[:]

        # Compute gap
        gap = abs(greedy_wait - best_wait) / max(best_wait, 1) * 100
        node = graph.get_node(node_id)

        case_info = {
            "intersection": node.name if node else f"Node {node_id}",
            "phases": num_phases,
            "flows": [round(f, 1) for f in incoming_flows],
            "greedy_greens": greedy_greens,
            "optimal_greens": best_greens,
            "greedy_wait": round(greedy_wait, 1),
            "optimal_wait": round(best_wait, 1),
            "gap_pct": round(gap, 2),
        }

        if gap < 1.0:
            optimal_cases.append(case_info)
        else:
            suboptimal_cases.append(case_info)

    # Summary statistics
    all_gaps = [c["gap_pct"] for c in optimal_cases + suboptimal_cases]
    avg_gap = sum(all_gaps) / max(len(all_gaps), 1)
    max_gap = max(all_gaps) if all_gaps else 0

    return {
        "optimal_cases": optimal_cases,
        "suboptimal_cases": suboptimal_cases,
        "num_optimal": len(optimal_cases),
        "num_suboptimal": len(suboptimal_cases),
        "avg_gap_pct": round(avg_gap, 2),
        "max_gap_pct": round(max_gap, 2),
        "analysis": (
            f"Greedy is optimal for {len(optimal_cases)}/{len(optimal_cases)+len(suboptimal_cases)} "
            f"intersections. Average gap: {avg_gap:.1f}%. Suboptimal cases occur when "
            f"traffic flows are highly asymmetric — the proportional allocation over-serves "
            f"low-flow directions and under-serves high-flow ones. In the Egyptian context, "
            f"this is common at intersections near mosques (asymmetric Friday traffic), "
            f"souqs (market-day surges), and school zones (peak directional flow)."
        ),
    }


# ─── C. Resource Allocation ───────────────────────────────────────────────────

def allocate_emergency_vehicles(graph: TransportGraph,
                                 incidents: List[Dict]) -> Dict:
    """
    Greedy allocation: assign nearest available ambulance to each incident.

    Args:
        graph: TransportGraph
        incidents: list of {'location': node_id, 'severity': 1-10}

    Returns:
        allocation plan with assigned vehicles and estimated response times
    """
    from algorithms.shortest_path import dijkstra

    # Fixed hospitals/depots
    depots = [nid for nid, node in graph.nodes.items()
              if node.node_type == "hospital"]

    if not depots:
        return {"error": "No hospitals found"}

    allocations = []
    available_depots = list(depots)  # simplify: infinite vehicles per depot

    for incident in sorted(incidents, key=lambda x: -x["severity"]):
        best_depot = None
        best_time = float("inf")
        best_path = None

        for depot in available_depots:
            result = dijkstra(graph, depot, incident["location"], mode="emergency")
            if result["found"] and result["time"] < best_time:
                best_time = result["time"]
                best_depot = depot
                best_path = result

        if best_depot is not None:
            depot_node = graph.get_node(best_depot)
            target_node = graph.get_node(incident["location"])
            allocations.append({
                "incident_location": target_node.name if target_node else incident["location"],
                "severity": incident["severity"],
                "assigned_from": depot_node.name if depot_node else best_depot,
                "response_time_min": round(best_time, 1),
                "path": best_path["path"] if best_path else [],
            })

    return {
        "allocations": allocations,
        "total_incidents": len(incidents),
        "avg_response_time": round(
            sum(a["response_time_min"] for a in allocations) / max(len(allocations), 1), 1
        ),
    }

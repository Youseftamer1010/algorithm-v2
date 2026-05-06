# 🏙️ Cairo Smart Transportation Network Optimization System

A professional smart-city dashboard for optimizing the Cairo metropolitan transportation network. Built with **Next.js 14 + TypeScript + TailwindCSS** (frontend), **FastAPI** (backend), **Leaflet/OpenStreetMap** (maps), and **scikit-learn** (ML).

---

## 🏗️ Architecture

```
┌──────────────────────┐       ┌──────────────────────┐
│   Next.js Frontend   │  API  │   FastAPI Backend    │
│   (port 3000)        │──────▶│   (port 8000)        │
│                      │       │                      │
│  • Leaflet/OSM maps  │       │  • Graph algorithms  │
│  • Race animation    │       │  • MST (Kruskal/Prim)│
│  • Recharts graphs   │       │  • Dijkstra / A*     │
│  • TailwindCSS UI    │       │  • DP optimization   │
│  • TypeScript        │       │  • ML predictor      │
└──────────────────────┘       │  • Simulation engine │
                               └──────────────────────┘
```

---

## 📦 Project Structure

```
smart_city/
├── main.py                         ← CLI test runner
├── report.md                       ← Technical report (CSE112)
├── Dockerfile                      ← Container build config
├── docker-compose.yml              ← Multi-service orchestration
├── .gitignore                      ← Git ignore rules
├── .dockerignore                   ← Docker build exclusions
│
├── backend/
│   ├── main.py                     ← FastAPI REST API server
│   └── requirements.txt            ← Backend-specific deps
│
├── frontend/
│   ├── package.json                ← Node.js dependencies
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── app/
│   │   ├── layout.tsx              ← Root layout + Leaflet CSS
│   │   ├── globals.css             ← Dark theme styles
│   │   ├── page.tsx                ← Dashboard home
│   │   ├── map/page.tsx            ← Live network map
│   │   ├── routes/page.tsx         ← Route finder (5 algorithms)
│   │   ├── race/page.tsx           ← Dijkstra vs A* race animation
│   │   ├── mst/page.tsx            ← MST network design
│   │   ├── simulation/page.tsx     ← Traffic simulation
│   │   ├── transit/page.tsx        ← Bus schedule DP optimizer
│   │   └── ml/page.tsx             ← ML congestion predictor
│   ├── components/
│   │   ├── MapView.tsx             ← Leaflet/OSM interactive map
│   │   ├── RaceAnimation.tsx       ← Step-by-step algorithm race
│   │   ├── Navbar.tsx              ← Navigation bar
│   │   └── MetricCard.tsx          ← KPI display card
│   └── lib/
│       └── api.ts                  ← API client + TypeScript types
│
├── data/
│   ├── cairo_data.py               ← Raw network data (nodes, edges, routes)
│   └── graph_model.py              ← OOP: Node, Edge, TransportGraph classes
│
├── algorithms/
│   ├── mst.py                      ← Kruskal + Prim MST
│   ├── shortest_path.py            ← Dijkstra, A*, Time-Dependent, K-Shortest, MemoizedRouter
│   └── optimization.py             ← Greedy signals, DP bus scheduling, DP road maintenance,
│                                     greedy analysis, emergency allocation
│
├── simulation/
│   ├── traffic_sim.py              ← Traffic state engine, scenarios, heatmap
│   └── ml_predictor.py             ← Random Forest congestion predictor
│
├── tests/
│   ├── test_graph_model.py
│   ├── test_mst.py
│   ├── test_shortest_path.py
│   ├── test_optimization.py
│   ├── test_simulation.py
│   └── test_ml_predictor.py
```

---

## 🚀 Quick Start

### 1. Install Python dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Start the FastAPI backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 3. Install frontend dependencies & start Next.js
```bash
cd frontend
npm install
npm run dev
```

### 4. Open the dashboard
Navigate to **http://localhost:3000**

### Alternative: Run CLI test suite
```bash
python main.py
pytest tests/ -v
```

### Alternative: Run with Docker
```bash
docker-compose up --build
```

---

## 🗺️ Dataset: Cairo Metropolitan Network

**25 Nodes** across:
- 12 Neighborhoods (Heliopolis, Nasr City, Maadi, Giza, etc.)
- 2 Hospitals (Cairo Int'l, Kasr El Aini)
- 3 Universities (Cairo, Ain Shams, AUC area)
- 1 Airport (Cairo International)
- 3 Metro Stations
- 4 Government/Commercial centers

**55 Edges** covering:
- Highways, main roads, city roads, metro lines
- 4 potential (unbuilt) roads for expansion planning

Each edge has: distance, capacity, condition (0-10), construction cost, base travel time, road type.

---

## 🧠 Algorithms

### A. Minimum Spanning Tree
| Algorithm | Complexity | Use Case |
|-----------|-----------|----------|
| Kruskal   | O(E log E) | Optimal network backbone with Union-Find |
| Prim      | O(E log V) | Growing tree from a seed node with min-heap |

Both support:
- **Facility priority weighting** — 40% discount for edges touching hospitals/airports
- **Potential roads** — include unbuilt roads for expansion planning

### B. Shortest Path
| Algorithm | Complexity | Mode |
|-----------|-----------|------|
| Dijkstra | O((V+E) log V) | Standard car routing |
| Time-Dependent Dijkstra | O((V+E) log V) | Traffic changes during journey |
| A* | O(E log V) avg | Emergency routing with Euclidean heuristic |
| Yen's K-Shortest | O(kV(V+E log V)) | Alternative route generation |
| ML-Aware Dijkstra | O((V+E) log V) | ML-predicted congestion adjusts edge weights |

### C. Traffic Signal Optimization (Greedy)
- Allocates green time proportional to incoming traffic flow
- Emergency preemption: 90s green for emergency direction
- Efficiency score based on cycle variance
- **Greedy optimality analysis** — identifies suboptimal cases

### D. Bus Schedule Optimization (Dynamic Programming)
- Finds optimal headway minimizing total passenger-minutes
- Balances fleet size vs. wait time
- DP state: (stop_index, buses_remaining)
- Fallback to uniform allocation when buses insufficient

### E. Road Maintenance Optimization (Dynamic Programming)
- Allocates budget across roads maximizing condition improvement
- DP state: (road_index, budget_remaining)

### F. Resource Allocation (Greedy)
- Assigns nearest hospital to each emergency incident
- Priority ordering by incident severity
- Memoized routing for repeated hospital→incident queries

---

## 🚗 Transportation Modes

| Mode | Traffic Effect | Use Case |
|------|---------------|----------|
| 🚗 Car | Full traffic multipliers | Standard routing |
| 🚑 Emergency | 70% traffic ignored | Ambulance/fire response |
| 🚌 Bus | 1.2× base time, partial traffic | Fixed-route transit |
| 🚇 Metro | Only metro-type edges affected | Rapid transit |

---

## 📊 Simulation Scenarios

| Scenario | Description |
|----------|-------------|
| Normal | Baseline traffic for time period |
| Morning Rush | Accidents on key arterials |
| Road Closure | 2 major roads closed |
| Emergency | Incidents requiring fast response |
| Peak Chaos | Multiple accidents + closures |

**Time Periods:** Morning (7–9am) · Afternoon (12–2pm) · Evening (5–8pm) · Night (10pm–1am)

---

## 🤖 Machine Learning

**Model:** Random Forest Regressor (scikit-learn)
- Trained on 2,000 synthetic traffic samples
- 8 features: hour, day, road type, capacity, condition, holiday, temperature, population
- Predicts congestion 0–1 for any road/time combination
- **ML-Aware Routing:** Predictions adjust edge weights for smarter path selection
- Integrated into route segment visualization

---

## 🎨 Dashboard Features (Next.js)

| Page | Contents |
|------|----------|
| 🏠 Dashboard | Network KPIs, route finder, interactive map |
| 🗺️ Live Map | Leaflet/OSM map with all nodes, edges, potential roads |
| �️ Routes | 5 algorithm options including ML-aware routing |
| ⚡ Race Animation | Side-by-side Dijkstra vs A* step-by-step visualization |
| 🌳 MST | Kruskal vs Prim comparison with map overlay |
| 📊 Simulation | Full-day traffic metrics across scenarios |
| 🚌 Transit | Bus schedule DP optimizer with segment allocation |
| � ML | Congestion predictor with feature importance bars |

---

## ⚡ Dijkstra vs A* Race Animation

The race animation page provides a **side-by-side comparison** of Dijkstra and A* search algorithms:
- Step-by-step visualization of explored nodes on the Leaflet map
- Play/pause/speed controls (0.5x to 5x)
- Real-time node count comparison
- Winner announcement with efficiency percentage

This demonstrates A*'s advantage: using the Euclidean distance heuristic, it typically explores **fewer nodes** than Dijkstra while finding the same optimal path.

---

## 📈 Complexity Summary

| Algorithm | Time | Space |
|-----------|------|-------|
| Kruskal MST | O(E log E) | O(V) |
| Prim MST | O(E log V) | O(V) |
| Dijkstra | O((V+E) log V) | O(V) |
| A* | O(E log V) avg | O(V) |
| Yen's k-paths | O(kN(E log V)) | O(kN) |
| Signal Greedy | O(V × degree) | O(V) |
| Bus DP | O(F × S) | O(S) |
| Maintenance DP | O(R × B) | O(R) |
| RF Predict | O(trees × depth) | O(model) |
| Memoized Router | O(1) hit / O((V+E)logV) miss | O(Q) |

---

## 🗂️ Key Design Decisions

1. **OOP Graph Model** — Nodes and Edges are first-class objects with rich methods
2. **Pluggable cost functions** — `edge.effective_weight(time, mode)` isolates routing logic
3. **Mode-aware routing** — Same graph, different cost functions per transport type
4. **Facility prioritization in MST** — Critical infrastructure gets lower effective weight
5. **Traffic state separation** — `TrafficState` encapsulates time-period + scenario
6. **Memoized routing** — Cache shortest-path queries for repeated hospital→incident lookups
7. **ML integration** — Random Forest predictions adjust edge weights for ML-aware routing
8. **Race animation** — Step-by-step algorithm exploration for educational visualization
9. **CartoDB Voyager light tiles** — Clean, professional light-themed map aesthetic for the dashboard

---

## 🚢 Deployment

### Frontend (Vercel)
```bash
cd frontend
vercel --prod
```
Set environment variable: `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com`

### Backend (Render)
```bash
# Render.com: Create a Web Service pointing to the repo
# Build Command: pip install -r backend/requirements.txt
# Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

---

## 📋 Sample Test Results

```
Airport → Maadi (Morning Rush):
  Dijkstra (car):     79.4 min, 33.5 km
  A* (emergency):     58.5 min, 33.5 km  ← 26% faster
  Time saved vs unoptimized: 27.8 min

Network (Evening Peak):
  Avg congestion: 70%
  Gridlock roads: 18
  Network score:  30/100

Bus Route B1 (Airport Express, 8 buses):
  Optimal headway: 23.4 min
  Wait time savings: 60.9% vs unoptimized

Dijkstra vs A* Race (Airport → Maadi):
  Dijkstra explored: 18 nodes
  A* explored:       12 nodes  ← 33% fewer nodes explored
```

---

## 🏆 CSE112 Bonus Coverage

| Bonus Criterion | Implementation |
|----------------|----------------|
| **ML-based traffic prediction** | Random Forest (scikit-learn) + ML-aware routing endpoint |
| **Side-by-side algorithm comparison** | Dijkstra vs A* race animation with step-by-step map visualization |
| **Live web app deployment** | Vercel (frontend) + Render (backend) |
| **Good README + Demo** | This README with architecture, screenshots, deployment guide |

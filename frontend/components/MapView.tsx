'use client'

import { useEffect, useRef, useCallback } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { GraphNode, GraphEdge } from '@/lib/api'

// Fix Leaflet default icon paths for Next.js/webpack
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

interface MapViewProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
  routeNodes?: number[]
  routeColor?: string
  mstEdges?: GraphEdge[]
  mstColor?: string
  mstEdges2?: GraphEdge[]
  mstColor2?: string
  visitedNodesDijkstra?: number[]
  visitedNodesAstar?: number[]
  currentNodeDijkstra?: number
  currentNodeAstar?: number
  raceMode?: string
  center?: [number, number]
  zoom?: number
  height?: string
}

const CAIRO_CENTER: [number, number] = [30.0444, 31.2357]

export default function MapView({
  nodes, edges, routeNodes = [], routeColor = '#1d3557',
  mstEdges = [], mstColor = '#e63946',
  mstEdges2 = [], mstColor2 = '#457b9d',
  visitedNodesDijkstra = [], visitedNodesAstar = [],
  currentNodeDijkstra, currentNodeAstar,
  raceMode = 'car',
  center = CAIRO_CENTER, zoom = 11, height = '600px',
}: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const layersRef = useRef<{
    nodes: L.LayerGroup
    edges: L.LayerGroup
    route: L.LayerGroup
    mst: L.LayerGroup
    mst2: L.LayerGroup
    dijkstraVisited: L.LayerGroup
    astarVisited: L.LayerGroup
  } | null>(null)
  const initDone = useRef(false)

  // Initialize map once
  useEffect(() => {
    if (!containerRef.current || initDone.current) return
    initDone.current = true

    const map = L.map(containerRef.current, {
      center, zoom, zoomControl: true,
    })

    // CartoDB Voyager light tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a> © <a href="https://carto.com/">CARTO</a>',
      subdomains: 'abcd', maxZoom: 19,
    }).addTo(map)

    layersRef.current = {
      nodes: L.layerGroup().addTo(map),
      edges: L.layerGroup().addTo(map),
      route: L.layerGroup().addTo(map),
      mst: L.layerGroup().addTo(map),
      mst2: L.layerGroup().addTo(map),
      dijkstraVisited: L.layerGroup().addTo(map),
      astarVisited: L.layerGroup().addTo(map),
    }

    mapRef.current = map

    // Force Leaflet to recalculate size after mount
    setTimeout(() => { map.invalidateSize() }, 200)

    return () => { map.remove(); mapRef.current = null; initDone.current = false }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Draw edges
  const drawEdges = useCallback(() => {
    if (!layersRef.current || !nodes.length) return
    layersRef.current.edges.clearLayers()
    edges.forEach(e => {
      if (e.is_potential) return
      const uNode = nodes.find(n => n.id === e.u)
      const vNode = nodes.find(n => n.id === e.v)
      if (!uNode || !vNode) return
      const color = e.color || '#1d3557'
      L.polyline([[uNode.lat, uNode.lon], [vNode.lat, vNode.lon]], {
        color, weight: 3, opacity: 0.8,
      }).bindPopup(`<b>${uNode.name} ↔ ${vNode.name}</b><br>${e.distance} km · ${e.road_type}`)
       .addTo(layersRef.current!.edges)
    })
  }, [edges, nodes])

  // Draw nodes
  const drawNodes = useCallback(() => {
    if (!layersRef.current || !nodes.length) return
    layersRef.current.nodes.clearLayers()
    nodes.forEach(n => {
      const size = n.importance >= 9 ? 16 : n.importance >= 7 ? 12 : 8
      const icon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="background:${n.color};width:${size}px;height:${size}px;border-radius:50%;border:2px solid #1d3557;box-shadow:0 0 6px ${n.color}88;"></div>`,
        iconSize: [size, size], iconAnchor: [size/2, size/2],
      })
      L.marker([n.lat, n.lon], { icon })
        .bindPopup(`<b>${n.name}</b><br>Type: ${n.type}<br>Pop: ${n.population.toLocaleString()}`)
        .addTo(layersRef.current!.nodes)
    })
  }, [nodes])

  // Draw route
  const drawRoute = useCallback(() => {
    if (!layersRef.current) return
    layersRef.current.route.clearLayers()
    if (!routeNodes.length) return
    const coords = routeNodes
      .map(id => nodes.find(n => n.id === id))
      .filter(Boolean)
      .map(n => [n!.lat, n!.lon] as [number, number])
    if (coords.length < 2) return
    L.polyline(coords, {
      color: routeColor, weight: 5, opacity: 0.9,
      dashArray: '10, 6',
    }).addTo(layersRef.current.route)
    mapRef.current?.fitBounds(L.latLngBounds(coords), { padding: [40, 40] })
  }, [routeNodes, nodes, routeColor])

  // Draw MST (first set)
  const drawMST = useCallback(() => {
    if (!layersRef.current) return
    layersRef.current.mst.clearLayers()
    mstEdges.forEach(e => {
      const uNode = nodes.find(n => n.id === e.u)
      const vNode = nodes.find(n => n.id === e.v)
      if (!uNode || !vNode) return
      L.polyline([[uNode.lat, uNode.lon], [vNode.lat, vNode.lon]], {
        color: mstColor, weight: 4.5, opacity: 0.9, dashArray: '8, 4',
      }).bindPopup(`<b>MST (${mstColor === '#e63946' ? 'Kruskal' : 'Prim'})</b><br>${uNode.name} ↔ ${vNode.name}`)
       .addTo(layersRef.current!.mst)
    })
  }, [mstEdges, nodes, mstColor])

  // Draw MST (second set — e.g. Prim)
  const drawMST2 = useCallback(() => {
    if (!layersRef.current) return
    layersRef.current.mst2.clearLayers()
    mstEdges2.forEach(e => {
      const uNode = nodes.find(n => n.id === e.u)
      const vNode = nodes.find(n => n.id === e.v)
      if (!uNode || !vNode) return
      L.polyline([[uNode.lat, uNode.lon], [vNode.lat, vNode.lon]], {
        color: mstColor2, weight: 4.5, opacity: 0.9, dashArray: '12, 6',
      }).bindPopup(`<b>MST (${mstColor2 === '#457b9d' ? 'Prim' : 'Kruskal'})</b><br>${uNode.name} ↔ ${vNode.name}`)
       .addTo(layersRef.current!.mst2)
    })
  }, [mstEdges2, nodes, mstColor2])

  // Vehicle emoji by mode
  const vehicleEmoji: Record<string, string> = { car: '🚗', emergency: '🚑', bus: '🚌', metro: '🚇' }

  // Draw race animation visited nodes
  const drawRace = useCallback(() => {
    if (!layersRef.current) return
    layersRef.current.dijkstraVisited.clearLayers()
    layersRef.current.astarVisited.clearLayers()

    const emoji = vehicleEmoji[raceMode] || '🚗'

    visitedNodesDijkstra.forEach(id => {
      const n = nodes.find(nd => nd.id === id)
      if (!n) return
      const isCurrent = id === currentNodeDijkstra
      if (isCurrent) {
        // Vehicle icon at current position
        const icon = L.divIcon({
          className: 'race-vehicle',
          html: `<div style="font-size:28px;filter:drop-shadow(0 0 6px #1d3557);transition:all 0.3s;">${emoji}</div>`,
          iconSize: [32, 32], iconAnchor: [16, 16],
        })
        L.marker([n.lat - 0.005, n.lon], { icon, zIndexOffset: 1000 })
          .addTo(layersRef.current!.dijkstraVisited)
      } else {
        // Small trail dot for visited nodes
        const icon = L.divIcon({
          className: 'race-marker',
          html: `<div style="background:#1d3557;width:8px;height:8px;border-radius:50%;opacity:0.6;"></div>`,
          iconSize: [8, 8], iconAnchor: [4, 4],
        })
        L.marker([n.lat - 0.005, n.lon], { icon })
          .addTo(layersRef.current!.dijkstraVisited)
      }
    })

    visitedNodesAstar.forEach(id => {
      const n = nodes.find(nd => nd.id === id)
      if (!n) return
      const isCurrent = id === currentNodeAstar
      if (isCurrent) {
        // Vehicle icon at current position
        const icon = L.divIcon({
          className: 'race-vehicle',
          html: `<div style="font-size:28px;filter:drop-shadow(0 0 6px #e63946);transition:all 0.3s;">${emoji}</div>`,
          iconSize: [32, 32], iconAnchor: [16, 16],
        })
        L.marker([n.lat + 0.005, n.lon], { icon, zIndexOffset: 1000 })
          .addTo(layersRef.current!.astarVisited)
      } else {
        // Small trail dot for visited nodes
        const icon = L.divIcon({
          className: 'race-marker',
          html: `<div style="background:#e63946;width:8px;height:8px;border-radius:50%;opacity:0.6;"></div>`,
          iconSize: [8, 8], iconAnchor: [4, 4],
        })
        L.marker([n.lat + 0.005, n.lon], { icon })
          .addTo(layersRef.current!.astarVisited)
      }
    })
  }, [visitedNodesDijkstra, visitedNodesAstar, currentNodeDijkstra, currentNodeAstar, nodes, raceMode])

  // Redraw on data changes
  useEffect(() => { drawEdges(); drawNodes(); drawRoute(); drawMST(); drawMST2(); drawRace() },
    [drawEdges, drawNodes, drawRoute, drawMST, drawMST2, drawRace])

  return (
    <div className="relative rounded-xl overflow-hidden border border-gray-300 shadow-md" style={{ height }}>
      <div ref={containerRef} style={{ height: '100%', width: '100%' }} />
      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-white/90 text-gray-800 rounded-lg p-3 text-xs space-y-1 pointer-events-none shadow-lg">
        {routeNodes.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 rounded" style={{ background: routeColor }}></div>
            <span>Route</span>
          </div>
        )}
        {mstEdges.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 rounded border-dashed" style={{ background: mstColor }}></div>
            <span>Kruskal MST</span>
          </div>
        )}
        {mstEdges2.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 rounded border-dashed" style={{ background: mstColor2 }}></div>
            <span>Prim MST</span>
          </div>
        )}
        {visitedNodesDijkstra.length > 0 && (
          <div className="flex items-center gap-2">
            <span style={{ fontSize: '14px' }}>{vehicleEmoji[raceMode] || '🚗'}</span>
            <span>Dijkstra ({raceMode})</span>
          </div>
        )}
        {visitedNodesAstar.length > 0 && (
          <div className="flex items-center gap-2">
            <span style={{ fontSize: '14px' }}>{vehicleEmoji[raceMode] || '🚗'}</span>
            <span>A* ({raceMode})</span>
          </div>
        )}
      </div>
    </div>
  )
}

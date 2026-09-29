import { useEffect, useState } from "react";
import {
  CircleMarker,
  MapContainer,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import { heatLayer } from "@linkurious/leaflet-heat";
import type { ThermalEvent } from "../types";
import type { MapFacilityFeature } from "../services/api";

import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";

const RISK_COLORS: Record<string, string> = {
  LOW: "#22c55e",
  MEDIUM: "#f59e0b",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

interface Props {
  events: ThermalEvent[];
  totalEventCount: number;
  onEventClick: (event: ThermalEvent) => void;
  selectedId?: string | null;
  facilities?: MapFacilityFeature[];
  onBoundsChange: (bounds: {
    minLon: number;
    minLat: number;
    maxLon: number;
    maxLat: number;
  }) => void;
}

/* -------------------------------------------------------
   HEATMAP
------------------------------------------------------- */

function HeatMap({ events }: { events: ThermalEvent[] }) {
  const map = useMap();

  useEffect(() => {
    const container = map.getContainer();

    if (container.clientWidth === 0 || container.clientHeight === 0) {
      return;
    }

    const heatPoints = events
      .filter(
        (event) =>
          Number.isFinite(event.latitude) && Number.isFinite(event.longitude),
      )
      .map(
        (event) =>
          [
            event.latitude,
            event.longitude,
            event.riskLevel === "CRITICAL"
              ? 1
              : event.riskLevel === "HIGH"
                ? 0.8
                : event.riskLevel === "MEDIUM"
                  ? 0.6
                  : 0.4,
          ] as [number, number, number],
      );

    if (heatPoints.length === 0) {
      return;
    }

    const layer = heatLayer(heatPoints, {
      radius: 25,
      blur: 20,
      maxZoom: 10,
      minOpacity: 0.35,
    });

    layer.addTo(map);

    return () => {
      if (map.hasLayer(layer)) {
        map.removeLayer(layer);
      }
    };
  }, [map, events]);

  return null;
}
/* -------------------------------------------------------
   MAP BOUNDS
------------------------------------------------------- */

function MapBoundsListener({
  onBoundsChange,
}: {
  onBoundsChange: (bounds: {
    minLon: number;
    minLat: number;
    maxLon: number;
    maxLat: number;
  }) => void;
}) {
  const map = useMap();

  useEffect(() => {
    const updateBounds = () => {
      const bounds = map.getBounds();

      onBoundsChange({
        minLon: bounds.getWest(),
        minLat: bounds.getSouth(),
        maxLon: bounds.getEast(),
        maxLat: bounds.getNorth(),
      });
    };

    updateBounds();

    map.on("moveend", updateBounds);
    map.on("zoomend", updateBounds);

    return () => {
      map.off("moveend", updateBounds);
      map.off("zoomend", updateBounds);
    };
  }, [map, onBoundsChange]);

  return null;
}

/* -------------------------------------------------------
   INDIA DEFAULT VIEW
------------------------------------------------------- */

function FitIndia() {
  const map = useMap();

  useEffect(() => {
    map.setView([22.5, 79], 5);
  }, [map]);

  return null;
}

/* -------------------------------------------------------
   ZOOM-AWARE DATA LAYERS
------------------------------------------------------- */

function ZoomAwareLayers({
  events,
  facilities,
  selectedId,
  onEventClick,
}: {
  events: ThermalEvent[];
  facilities: MapFacilityFeature[];
  selectedId?: string | null;
  onEventClick: (event: ThermalEvent) => void;
}) {
  const map = useMap();
  const [zoom, setZoom] = useState(map.getZoom());

  useEffect(() => {
    const updateZoom = () => {
      setZoom(map.getZoom());
    };

    updateZoom();

    map.on("zoomend", updateZoom);

    return () => {
      map.off("zoomend", updateZoom);
    };
  }, [map]);

  /*
   * India-wide view:
   * Only show the heatmap.
   *
   * Zoom 7+:
   * Show detailed FIRMS markers and OSM facilities.
   */
  const showDetailedLayers = zoom >= 7;

  if (!showDetailedLayers) {
    return null;
  }

  return (
    <>
      {/* FIRMS thermal events */}
      <MarkerClusterGroup
        chunkedLoading
        showCoverageOnHover={false}
        spiderfyOnMaxZoom={true}
        maxClusterRadius={35}
      >
        {events.map((evt) => {
          const color = RISK_COLORS[evt.riskLevel] ?? RISK_COLORS.LOW;

          const isSelected = selectedId === evt.id;
          const isCritical = evt.riskLevel === "CRITICAL";

          return (
            <CircleMarker
              key={evt.id}
              center={[evt.latitude, evt.longitude]}
              radius={isCritical ? 7 : isSelected ? 6 : 5}
              pathOptions={{
                color: isSelected ? "#ffffff" : color,
                fillColor: color,
                fillOpacity: 0.85,
                weight: isSelected ? 2 : 1,
              }}
              eventHandlers={{
                click: () => onEventClick(evt),
              }}
            >
              <Tooltip direction="top" offset={[0, -8]} opacity={0.96}>
                <div
                  style={{
                    minWidth: "190px",
                    fontFamily: "Inter, sans-serif",
                  }}
                >
                  <div
                    style={{
                      fontFamily: "monospace",
                      fontWeight: 700,
                      color: "#0891b2",
                      marginBottom: "6px",
                    }}
                  >
                    {evt.eventId}
                  </div>

                  <div
                    style={{
                      fontSize: "12px",
                      marginBottom: "5px",
                    }}
                  >
                    {evt.classification}
                  </div>

                  <div
                    style={{
                      fontFamily: "monospace",
                      fontSize: "11px",
                      color,
                      fontWeight: 700,
                    }}
                  >
                    {evt.riskLevel} · Score {evt.riskScore}
                  </div>

                  <div
                    style={{
                      fontSize: "10px",
                      marginTop: "5px",
                      color: "#64748b",
                    }}
                  >
                    {evt.latitude.toFixed(4)}° N, {evt.longitude.toFixed(4)}° E
                  </div>

                  <div
                    style={{
                      fontSize: "10px",
                      marginTop: "3px",
                      color: "#64748b",
                    }}
                  >
                    {evt.satellite} · {evt.instrument}
                  </div>
                </div>
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MarkerClusterGroup>

      {/* OSM industrial facilities */}
      {facilities.map((facility) => {
        const coordinates = facility.geometry.coordinates;

        const longitude = coordinates[0];
        const latitude = coordinates[1];

        return (
          <CircleMarker
            key={facility.properties.facilityId}
            center={[latitude, longitude]}
            radius={5}
            pathOptions={{
              color: "#38bdf8",
              fillColor: "#0f3557",
              fillOpacity: 0.9,
              weight: 1,
            }}
          >
            <Tooltip direction="top" opacity={0.95}>
              <div
                style={{
                  fontFamily: "Inter, sans-serif",
                  minWidth: "150px",
                }}
              >
                <div
                  style={{
                    fontFamily: "monospace",
                    fontWeight: 700,
                    color: "#0891b2",
                  }}
                >
                  INDUSTRIAL FACILITY
                </div>

                <div
                  style={{
                    marginTop: "5px",
                    fontSize: "12px",
                  }}
                >
                  {facility.properties.name || "Unnamed facility"}
                </div>

                <div
                  style={{
                    marginTop: "4px",
                    fontSize: "10px",
                    color: "#64748b",
                  }}
                >
                  {facility.properties.facilityType || "Industrial"}
                </div>
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </>
  );
}

/* -------------------------------------------------------
   MAIN MAP
------------------------------------------------------- */

export default function IndiaMap({
  events,
  totalEventCount,
  onEventClick,
  selectedId,
  facilities = [],
  onBoundsChange,
}: Props) {
  return (
    <div className="relative w-full h-full bg-[#050a14] overflow-hidden">
      <MapContainer
        center={[22.5, 79]}
        zoom={5}
        minZoom={4}
        maxZoom={12}
        scrollWheelZoom={true}
        className="w-full h-full"
        zoomControl={true}
      >
        {/* OpenStreetMap base layer */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <FitIndia />

        <MapBoundsListener onBoundsChange={onBoundsChange} />

        {/* Heatmap is always visible */}
        <HeatMap events={events} />

        {/* Detailed markers only when zoomed in */}
        <ZoomAwareLayers
          events={events}
          facilities={facilities}
          selectedId={selectedId}
          onEventClick={onEventClick}
        />
      </MapContainer>

      {/* Map title */}
      <div className="absolute top-3 left-3 z-[1000] glass px-3 py-2">
        <div className="font-mono-data text-[10px] text-[#38bdf8] tracking-widest">
          NASA FIRMS · THERMAL DETECTIONS
        </div>

        <div className="font-mono-data text-[9px] text-[#7a9cc4] mt-1">
          INDIA · LIVE INTELLIGENCE MAP
        </div>
      </div>

      {/* Event count */}
      <div className="absolute top-3 right-3 z-[1000] glass px-3 py-1.5">
        <span className="font-mono-data text-[10px] text-[#7a9cc4] tracking-widest">
          {totalEventCount.toLocaleString()} DETECTIONS
        </span>
      </div>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 z-[1000] glass px-3 py-2 flex items-center gap-4">
        {(["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const).map((risk) => (
          <div key={risk} className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{
                background: RISK_COLORS[risk],
              }}
            />

            <span
              className="font-mono-data text-[10px] tracking-widest"
              style={{
                color: RISK_COLORS[risk],
              }}
            >
              {risk}
            </span>
          </div>
        ))}

        <div className="flex items-center gap-1.5 ml-2 border-l border-[#1e3a5f] pl-3">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{
              background: "#0f3557",
              border: "1px solid #38bdf8",
            }}
          />

          <span className="font-mono-data text-[10px] text-[#3d6490] tracking-widest">
            FACILITY
          </span>
        </div>
      </div>
    </div>
  );
}

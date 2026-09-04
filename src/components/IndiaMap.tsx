import { useState } from "react";
import type { ThermalEvent } from "../types";
import RiskBadge from "./RiskBadge";

// Approximate India bounding box: lat 8–37, lon 68–98
// Map SVG viewport: 600x620
const MAP_W = 600;
const MAP_H = 620;
const LAT_MIN = 6.5,
  LAT_MAX = 37.5;
const LON_MIN = 67.5,
  LON_MAX = 98.5;

function toXY(lat: number, lon: number) {
  const x = ((lon - LON_MIN) / (LON_MAX - LON_MIN)) * MAP_W;
  const y = ((LAT_MAX - lat) / (LAT_MAX - LAT_MIN)) * MAP_H;
  return { x, y };
}

const RISK_COLORS: Record<string, string> = {
  LOW: "#22c55e",
  MEDIUM: "#f59e0b",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

// Simplified India SVG path (approximate outline)
const INDIA_PATH = `M 162,42 L 175,38 L 188,44 L 202,40 L 215,48 L 228,44 L 242,52 L 255,50 L 268,58 L 280,56 L 292,64 L 302,60 L 314,68 L 322,80 L 330,76 L 342,84 L 348,96 L 360,92 L 368,104 L 374,118 L 382,110 L 390,124 L 395,138 L 400,152 L 406,164 L 410,180 L 415,194 L 418,210 L 415,226 L 410,238 L 416,252 L 418,268 L 415,282 L 412,296 L 408,310 L 402,324 L 395,338 L 388,350 L 380,362 L 370,374 L 360,384 L 348,394 L 336,402 L 322,410 L 308,416 L 294,420 L 280,424 L 266,425 L 252,424 L 238,422 L 224,418 L 210,412 L 198,404 L 186,394 L 176,383 L 166,370 L 158,356 L 154,342 L 150,328 L 148,314 L 145,300 L 142,286 L 140,272 L 138,258 L 136,244 L 135,230 L 135,216 L 136,202 L 138,188 L 140,174 L 143,160 L 146,148 L 150,136 L 154,124 L 155,112 L 153,100 L 148,90 L 145,78 L 150,66 L 155,56 L 162,42 Z`;

interface Props {
  events: ThermalEvent[];
  onEventClick: (event: ThermalEvent) => void;
  selectedId?: string | null;
}

export default function IndiaMap({ events, onEventClick, selectedId }: Props) {
  const [tooltip, setTooltip] = useState<{
    event: ThermalEvent;
    x: number;
    y: number;
  } | null>(null);

  return (
    <div className="relative w-full h-full bg-[#050a14] overflow-hidden">
      {/* Grid overlay */}
      <div className="absolute inset-0 grid-bg opacity-40 pointer-events-none" />

      <svg
        viewBox={`0 0 ${MAP_W} ${MAP_H}`}
        className="w-full h-full"
        style={{ maxHeight: "100%" }}
      >
        {/* Ocean fill */}
        <rect width={MAP_W} height={MAP_H} fill="#050a14" />

        {/* India outline */}
        <path
          d={INDIA_PATH}
          fill="#0a1628"
          stroke="#1e3a5f"
          strokeWidth="1.5"
        />

        {/* State border suggestions */}
        <line
          x1="200"
          y1="150"
          x2="200"
          y2="420"
          stroke="#122035"
          strokeWidth="0.5"
          strokeDasharray="3,4"
        />
        <line
          x1="250"
          y1="100"
          x2="280"
          y2="420"
          stroke="#122035"
          strokeWidth="0.5"
          strokeDasharray="3,4"
        />
        <line
          x1="140"
          y1="220"
          x2="410"
          y2="220"
          stroke="#122035"
          strokeWidth="0.5"
          strokeDasharray="3,4"
        />
        <line
          x1="140"
          y1="300"
          x2="410"
          y2="300"
          stroke="#122035"
          strokeWidth="0.5"
          strokeDasharray="3,4"
        />

        {/* Facility markers */}
        {[
          { lat: 21.18, lon: 72.81 },
          { lat: 22.57, lon: 88.36 },
          { lat: 18.98, lon: 79.53 },
          { lat: 20.31, lon: 85.86 },
          { lat: 22.09, lon: 85.83 },
          { lat: 17.69, lon: 83.22 },
          { lat: 13.08, lon: 80.27 },
          { lat: 19.08, lon: 72.88 },
          { lat: 24.06, lon: 82.66 },
          { lat: 22.42, lon: 70.05 },
        ].map((f, i) => {
          const { x, y } = toXY(f.lat, f.lon);
          return (
            <rect
              key={i}
              x={x - 3}
              y={y - 3}
              width={6}
              height={6}
              fill="#1e3a5f"
              stroke="#2d5a8e"
              strokeWidth="0.5"
              opacity="0.7"
            />
          );
        })}

        {/* Event markers */}
        {events.map((evt) => {
          const { x, y } = toXY(evt.latitude, evt.longitude);
          const color = RISK_COLORS[evt.riskLevel];
          const isSelected = selectedId === evt.id;
          const isCritical = evt.riskLevel === "CRITICAL";

          return (
            <g
              key={evt.id}
              onClick={() => onEventClick(evt)}
              style={{ cursor: "pointer" }}
              onMouseEnter={(e) => {
                const rect = (
                  e.currentTarget.closest("svg") as SVGSVGElement
                ).getBoundingClientRect();
                const svgEl = e.currentTarget.closest("svg") as SVGSVGElement;
                const pt = svgEl.createSVGPoint();
                pt.x = e.clientX;
                pt.y = e.clientY;
                const svgPt = pt.matrixTransform(
                  svgEl.getScreenCTM()!.inverse(),
                );
                setTooltip({ event: evt, x: svgPt.x, y: svgPt.y });
              }}
              onMouseLeave={() => setTooltip(null)}
            >
              {/* Pulse ring for critical */}
              {isCritical && (
                <circle
                  cx={x}
                  cy={y}
                  r={12}
                  fill="none"
                  stroke={color}
                  strokeWidth="1"
                  opacity="0.3"
                  className="event-pulse-ring"
                />
              )}
              {/* Selection ring */}
              {isSelected && (
                <circle
                  cx={x}
                  cy={y}
                  r={10}
                  fill="none"
                  stroke={color}
                  strokeWidth="1.5"
                  opacity="0.8"
                />
              )}
              {/* Main dot */}
              <circle
                cx={x}
                cy={y}
                r={isCritical ? 6 : 4.5}
                fill={color}
                fillOpacity={0.9}
                stroke={isSelected ? "#fff" : color}
                strokeWidth={isSelected ? 1.5 : 0.5}
              />
              {/* Inner dot */}
              <circle
                cx={x}
                cy={y}
                r={isCritical ? 2.5 : 1.5}
                fill="#fff"
                fillOpacity="0.8"
              />
            </g>
          );
        })}

        {/* Tooltip */}
        {tooltip &&
          (() => {
            const { event: evt, x, y } = tooltip;
            const color = RISK_COLORS[evt.riskLevel];
            const tw = 180,
              th = 64;
            const tx = Math.min(x + 12, MAP_W - tw - 8);
            const ty = Math.max(y - 32, 4);
            return (
              <g pointerEvents="none">
                <rect
                  x={tx}
                  y={ty}
                  width={tw}
                  height={th}
                  rx="2"
                  fill="#0d1f3c"
                  stroke="#1e3a5f"
                  strokeWidth="0.5"
                />
                <rect x={tx} y={ty} width={tw} height={2} rx="1" fill={color} />
                <text
                  x={tx + 10}
                  y={ty + 18}
                  fill="#e2eaf5"
                  fontSize="10"
                  fontFamily="'JetBrains Mono'"
                  fontWeight="500"
                >
                  {evt.eventId}
                </text>
                <text
                  x={tx + 10}
                  y={ty + 32}
                  fill="#7a9cc4"
                  fontSize="9"
                  fontFamily="Inter"
                >
                  {evt.classification.slice(0, 28)}
                </text>
                <text
                  x={tx + 10}
                  y={ty + 50}
                  fill={color}
                  fontSize="9"
                  fontFamily="'JetBrains Mono'"
                  fontWeight="500"
                >
                  {evt.riskLevel} · Score {evt.riskScore}
                </text>
              </g>
            );
          })()}
      </svg>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 glass px-3 py-2 flex items-center gap-4">
        {(["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const).map((r) => (
          <div key={r} className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{ background: RISK_COLORS[r] }}
            />
            <span
              className="font-mono-data text-[10px] tracking-widest"
              style={{ color: RISK_COLORS[r] }}
            >
              {r}
            </span>
          </div>
        ))}
        <div className="flex items-center gap-1.5 ml-2 border-l border-[#1e3a5f] pl-3">
          <span className="w-3 h-3 border border-[#2d5a8e] bg-[#1e3a5f] inline-block" />
          <span className="font-mono-data text-[10px] text-[#3d6490] tracking-widest">
            FACILITY
          </span>
        </div>
      </div>

      {/* Event count */}
      <div className="absolute top-3 right-3 glass px-3 py-1.5">
        <span className="font-mono-data text-[10px] text-[#7a9cc4] tracking-widest">
          {events.length} DETECTIONS
        </span>
      </div>
    </div>
  );
}

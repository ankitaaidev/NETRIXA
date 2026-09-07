import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Flame, AlertTriangle, Building2, Activity, Eye, TrendingUp } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import IndiaMap from '../components/IndiaMap';
import RiskBadge from '../components/RiskBadge';
import { DASHBOARD_SUMMARY } from '../data/mockData';
import { api, type MapFacilityFeature } from '../services/api';
import { useAppStore } from '../store';
import type { ThermalEvent } from '../types';

const KPI = [
  { label: 'Total Thermal Events', value: DASHBOARD_SUMMARY.totalEvents.toLocaleString(), sub: 'FIRMS detections processed', icon: Flame, accent: 'cyan' },
  { label: 'Industrial Context', value: DASHBOARD_SUMMARY.industrialEvents.toLocaleString(), sub: 'Near industrial facilities', icon: Building2, accent: 'cyan' },
  { label: 'Potential Ind. Fires', value: DASHBOARD_SUMMARY.potentialIndustrialFires.toString(), sub: 'AI-flagged anomalies', icon: AlertTriangle, accent: 'orange' },
  { label: 'Critical Events', value: DASHBOARD_SUMMARY.criticalEvents.toString(), sub: 'Risk score > 75', icon: AlertTriangle, accent: 'red' },
  { label: 'Persistent Sources', value: DASHBOARD_SUMMARY.persistentSources.toString(), sub: 'Recurring thermal activity', icon: Activity, accent: 'amber' },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass px-3 py-2 text-xs">
      <div className="font-mono-data text-[10px] text-[#7a9cc4] mb-1">{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="font-mono-data text-[10px]" style={{ color: p.color }}>{p.name}: {p.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { events, eventsError } = useAppStore();
  const [selectedEvent, setSelectedEvent] = useState<ThermalEvent | null>(null);
  const [summary, setSummary] = useState(DASHBOARD_SUMMARY);
  const [mapEventIds, setMapEventIds] = useState<string[] | null>(null);
  const [facilities, setFacilities] = useState<MapFacilityFeature[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    void Promise.all([api.getDashboardSummary(), api.getMapEvents(), api.getMapFacilities()]).then(([nextSummary, mapEvents, mapFacilities]) => {
      if (!active) return;
      setSummary(nextSummary);
      setMapEventIds(mapEvents.features.map((feature) => feature.properties.eventId));
      setFacilities(mapFacilities.features);
      setLoading(false);
    }).catch(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  const mapEvents = useMemo(() => {
    if (!mapEventIds) return events;
    const ids = new Set(mapEventIds);
    return events.filter((event) => ids.has(event.eventId));
  }, [events, mapEventIds]);

  const trend = useMemo(() => {
    const days = Array.from({ length: 14 }, (_, index) => {
      const date = new Date();
      date.setDate(date.getDate() - (13 - index));
      const key = date.toISOString().slice(0, 10);
      const dayEvents = events.filter((event) => event.acquisitionDate === key);
      return {
        date: date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
        total: dayEvents.length,
        industrial: dayEvents.filter((event) => event.industrialProximity === 'HIGH' || event.industrialProximity === 'MEDIUM').length,
        critical: dayEvents.filter((event) => event.riskLevel === 'CRITICAL').length,
      };
    });
    return days;
  }, [events]);

  const riskDistribution = useMemo(() => (['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((level) => ({
    level,
    count: events.filter((event) => event.riskLevel === level).length,
    color: level === 'CRITICAL' ? '#ef4444' : level === 'HIGH' ? '#f97316' : level === 'MEDIUM' ? '#f59e0b' : '#22c55e',
  })), [events]);

  const handleEventClick = (evt: ThermalEvent) => setSelectedEvent(evt);

  return (
    <div className="flex flex-col h-full bg-[#050a14]">
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#1e3a5f] flex items-start justify-between flex-shrink-0">
        <div>
          <div className="font-display font-700 text-2xl tracking-[0.12em] text-[#e2eaf5]">THERMAL INTELLIGENCE CENTER</div>
          <div className="font-mono-data text-[11px] text-[#3d6490] tracking-widest mt-0.5">
            NATIONAL-SCALE MONITORING OF THERMAL ANOMALIES AND INDUSTRIAL RISK · INDIA 2026
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="font-mono-data text-[10px] text-green-400 tracking-widest">LIVE · 03:50 UTC</span>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-5 gap-0 border-b border-[#1e3a5f] flex-shrink-0">
        {KPI.map((k) => (
          <div key={k.label} className={`kpi-card ${k.accent} border-r border-[#1e3a5f] last:border-r-0`}>
            <div className="flex items-start justify-between">
              <div>
                <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest uppercase mb-1">{k.label}</div>
                <div className="font-display font-700 text-3xl text-[#e2eaf5] leading-none">{k.value}</div>
                <div className="font-mono-data text-[9px] text-[#3d6490] mt-1 tracking-wide">{k.sub}</div>
              </div>
              <k.icon size={16} className={
                k.accent === 'red' ? 'text-red-400 opacity-60' :
                k.accent === 'orange' ? 'text-orange-400 opacity-60' :
                k.accent === 'amber' ? 'text-amber-400 opacity-60' :
                'text-cyan-400 opacity-60'
              } />
            </div>
          </div>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 flex min-h-0">
        {/* Map */}
        <div className="flex-1 relative min-w-0">
          <IndiaMap events={mapEvents} facilities={facilities} onEventClick={handleEventClick} selectedId={selectedEvent?.eventId} />
          {(loading || eventsError) && <div className="absolute top-3 left-3 glass px-3 py-1.5 font-mono-data text-[10px] text-amber-400">{loading ? 'SYNCING MAP DATA...' : 'DEMO MAP DATA ACTIVE'}</div>}

          {/* Event preview panel */}
          {selectedEvent && (
            <div className="absolute top-3 right-3 w-64 glass z-10">
              {/* Risk stripe */}
              <div className={`h-1 ${
                selectedEvent.riskLevel === 'CRITICAL' ? 'bg-red-500' :
                selectedEvent.riskLevel === 'HIGH' ? 'bg-orange-500' :
                selectedEvent.riskLevel === 'MEDIUM' ? 'bg-amber-500' : 'bg-green-500'
              }`} />
              <div className="p-3">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="font-mono-data text-[10px] text-[#7a9cc4] tracking-widest">{selectedEvent.eventId}</div>
                    <div className="font-display font-600 text-sm text-[#e2eaf5] mt-0.5 leading-tight">{selectedEvent.classification}</div>
                  </div>
                  <button onClick={() => setSelectedEvent(null)}
                    className="text-[#3d6490] hover:text-[#7a9cc4] text-xs leading-none ml-2 mt-0.5">✕</button>
                </div>

                <RiskBadge level={selectedEvent.riskLevel} pulse size="sm" />

                <div className="mt-3 space-y-1.5 border-t border-[#122035] pt-2">
                  {[
                    ['Confidence', `${selectedEvent.confidence}%`],
                    ['Risk Score', `${selectedEvent.riskScore} / 100`],
                    selectedEvent.facilityName
                      ? ['Nearest Facility', `${selectedEvent.facilityDistance} m`]
                      : ['Land Cover', selectedEvent.landCover],
                    ['Historical Deviation', `${selectedEvent.zScore > 2 ? 'HIGH' : selectedEvent.zScore > 1 ? 'MEDIUM' : 'LOW'} (z=${selectedEvent.zScore}σ)`],
                    ['Observations', `${selectedEvent.observations}`],
                  ].map(([k, v]) => (
                    <div key={k} className="flex justify-between items-center">
                      <span className="font-mono-data text-[9px] text-[#3d6490] tracking-wide">{k}</span>
                      <span className="font-mono-data text-[10px] text-[#7a9cc4]">{v}</span>
                    </div>
                  ))}
                </div>

                <button
                  onClick={() => navigate(`/events/${selectedEvent.eventId}`)}
                  className="mt-3 w-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-display font-600 text-xs tracking-widest py-1.5 hover:bg-cyan-500/20 transition-colors"
                >
                  INVESTIGATE EVENT →
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right panel */}
        <div className="w-72 flex flex-col border-l border-[#1e3a5f] flex-shrink-0 overflow-y-auto">
          {/* Trend chart */}
          <div className="p-4 border-b border-[#1e3a5f]">
            <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">14-DAY EVENT TREND</div>
            <ResponsiveContainer width="100%" height={100}>
              <AreaChart data={trend} margin={{ top: 0, right: 0, left: -30, bottom: 0 }}>
                <defs>
                  <linearGradient id="gTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gInd" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 4" stroke="#1e3a5f" strokeOpacity={0.4} />
                <XAxis dataKey="date" tick={{ fontSize: 8, fill: '#3d6490', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} interval={6} />
                <YAxis tick={{ fontSize: 8, fill: '#3d6490', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="total" name="Total" stroke="#38bdf8" strokeWidth={1.5} fill="url(#gTotal)" dot={false} />
                <Area type="monotone" dataKey="industrial" name="Industrial" stroke="#f97316" strokeWidth={1.5} fill="url(#gInd)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Recent critical */}
          <div className="p-4 flex-1">
            <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">CRITICAL & HIGH EVENTS</div>
            <div className="space-y-2">
              {events.filter((e) => e.riskLevel === 'CRITICAL' || e.riskLevel === 'HIGH')
                .slice(0, 6)
                .map((evt) => (
                  <div key={evt.eventId}
                    className="data-row p-2 border border-[#122035] cursor-pointer"
                    onClick={() => navigate(`/events/${evt.eventId}`)}>
                    <div className="flex items-start justify-between gap-1 mb-1">
                      <span className="font-mono-data text-[10px] text-cyan-400">{evt.eventId}</span>
                      <RiskBadge level={evt.riskLevel} size="sm" />
                    </div>
                    <div className="font-display text-xs text-[#7a9cc4] leading-tight">{evt.classification}</div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="font-mono-data text-[9px] text-[#3d6490]">{evt.state}</span>
                      <span className="font-mono-data text-[9px] text-[#3d6490]">Score {evt.riskScore}</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Risk distribution */}
          <div className="p-4 border-t border-[#1e3a5f]">
            <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">RISK DISTRIBUTION</div>
            {riskDistribution.map(({ level, count, color }) => (
              <div key={level} className="mb-2">
                <div className="flex justify-between mb-0.5">
                  <span className="font-mono-data text-[9px] tracking-widest" style={{ color }}>{level}</span>
                  <span className="font-mono-data text-[9px] text-[#3d6490]">{count}</span>
                </div>
                <div className="h-1 bg-[#0a1628] w-full">
                  <div className="h-full" style={{ width: `${events.length ? (count / events.length) * 100 : 0}%`, background: color, opacity: 0.7 }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

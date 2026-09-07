import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import type { ThermalEvent } from '../types';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass px-3 py-2 text-xs">
      <div className="font-mono-data text-[9px] text-[#7a9cc4] mb-1">{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} className="font-mono-data text-[10px]" style={{ color: p.color || p.fill }}>{p.name}: {p.value}</div>
      ))}
    </div>
  );
};

export default function HistoricalIntelligence() {
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    void api.getAllEvents().then((nextEvents) => {
      if (active) { setEvents(nextEvents); setLoading(false); }
    }).catch(() => {
      if (active) { setError(true); setLoading(false); }
    });
    return () => { active = false; };
  }, []);

  const daily = useMemo(() => Array.from({ length: 30 }, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() - (29 - index));
    const key = date.toISOString().slice(0, 10);
    const dayEvents = events.filter((event) => event.acquisitionDate === key);
    return {
      date: date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
      total: dayEvents.length,
      industrial: dayEvents.filter((event) => event.industrialProximity === 'HIGH' || event.industrialProximity === 'MEDIUM').length,
      agricultural: dayEvents.filter((event) => event.classification === 'Agricultural Burning').length,
    };
  }), [events]);

  const classDist = useMemo(() => {
    const counts = new Map<string, number>();
    events.forEach((event) => counts.set(event.classification, (counts.get(event.classification) || 0) + 1));
    const colors = ['#38bdf8', '#22c55e', '#ef4444', '#f97316', '#f59e0b', '#7a9cc4', '#3d6490'];
    return Array.from(counts.entries()).map(([name, value], index) => ({ name, value, color: colors[index % colors.length] }));
  }, [events]);

  const hotspots = useMemo(() => {
    const grouped = new Map<string, ThermalEvent[]>();
    events.filter((event) => event.facilityName).forEach((event) => {
      const current = grouped.get(event.facilityName!) || [];
      grouped.set(event.facilityName!, [...current, event]);
    });
    return Array.from(grouped.entries()).sort((a, b) => b[1].length - a[1].length).slice(0, 10);
  }, [events]);

  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#1e3a5f] flex-shrink-0">
        <div className="font-display font-700 text-xl tracking-[0.1em] text-[#e2eaf5]">HISTORICAL INTELLIGENCE</div>
        <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest">THERMAL EVENT PATTERNS · INDIA · OCT 2025 – SEP 2026</div>
      </div>
      {error && <div className="px-5 py-2 border-b border-amber-800/40 bg-amber-950/20 font-mono-data text-[10px] text-amber-400">BACKEND UNAVAILABLE · HISTORICAL AGGREGATES UNAVAILABLE</div>}
      {loading && <div className="px-5 py-2 font-mono-data text-[10px] text-cyan-400">LOADING HISTORICAL EVENT DATA...</div>}

      <div className="p-5 space-y-4">
        {/* Daily events */}
        <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
          <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">30-DAY DAILY EVENT VOLUME</div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={daily} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gT" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gI" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="2 4" stroke="#1e3a5f" strokeOpacity={0.3} />
              <XAxis dataKey="date" tick={{ fontSize: 8, fill: '#3d6490', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} interval={6} />
              <YAxis tick={{ fontSize: 8, fill: '#3d6490', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="total" name="Total Events" stroke="#38bdf8" strokeWidth={1.5} fill="url(#gT)" dot={false} />
              <Area type="monotone" dataKey="agricultural" name="Agricultural" stroke="#22c55e" strokeWidth={1} fill="none" dot={false} strokeDasharray="3 3" />
              <Area type="monotone" dataKey="industrial" name="Industrial" stroke="#ef4444" strokeWidth={1.5} fill="url(#gI)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Classification distribution */}
          <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
            <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">EVENT CLASSIFICATION DISTRIBUTION</div>
            <div className="flex items-center gap-4">
              <PieChart width={160} height={160}>
                <Pie data={classDist} dataKey="value" cx={75} cy={75} outerRadius={70} innerRadius={40} strokeWidth={0}>
                  {classDist.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
              <div className="flex-1 space-y-1.5">
                {classDist.map(({ name, value, color }) => (
                  <div key={name} className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color }} />
                    <span className="font-mono-data text-[9px] text-[#7a9cc4] flex-1 truncate">{name}</span>
                    <span className="font-mono-data text-[9px] text-[#3d6490]">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Risk over time */}
          <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
            <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">RISK LEVEL DISTRIBUTION OVER TIME</div>
            <div className="h-[180px] flex items-center justify-center font-mono-data text-[10px] text-[#3d6490] text-center">NO HISTORICAL RISK-TREND ENDPOINT AVAILABLE</div>
          </div>
        </div>

        {/* Persistent hotspots */}
        <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
          <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">PERSISTENT THERMAL HOTSPOTS — TOP 10 RECURRING LOCATIONS</div>
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#1e3a5f]">
                {['Location', 'State', 'Type', 'Observations', '90-day Mean', 'Status'].map((h) => (
                  <th key={h} className="px-3 py-2 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {hotspots.map(([facilityName, facilityEvents]) => {
                const event = facilityEvents[0];
                const status = event.riskLevel === 'CRITICAL' ? 'CRITICAL' : event.riskLevel === 'HIGH' ? 'ABNORMAL' : event.riskLevel === 'MEDIUM' ? 'WATCH' : 'NORMAL';
                return [facilityName, event.state, event.facilityType || 'Industrial', facilityEvents.length, event.historicalMean ? `${event.historicalMean.toFixed(0)} K` : '—', status];
              }).map(([loc, state, type, obs, mean, status]) => (
                <tr key={loc as string} className="data-row border-b border-[#0d1f3c]">
                  <td className="px-3 py-2 font-display font-500 text-[11px] text-[#e2eaf5]">{loc as string}</td>
                  <td className="px-3 py-2 font-mono-data text-[10px] text-[#7a9cc4]">{state as string}</td>
                  <td className="px-3 py-2 font-mono-data text-[10px] text-[#7a9cc4]">{type as string}</td>
                  <td className="px-3 py-2 font-mono-data text-[10px] text-[#7a9cc4]">{obs as number}</td>
                  <td className="px-3 py-2 font-mono-data text-[10px] text-[#7a9cc4]">{mean as string}</td>
                  <td className="px-3 py-2 font-mono-data text-[10px]">
                    <span className={
                      status === 'NORMAL' ? 'text-green-400' :
                      status === 'WATCH' ? 'text-amber-400' :
                      status === 'ABNORMAL' ? 'text-orange-400' : 'text-red-400'
                    }>{status as string}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

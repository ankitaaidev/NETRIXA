import { useNavigate } from 'react-router-dom';
import { Filter, Search, X } from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import { useAppStore } from '../store';
import type { RiskLevel } from '../types';

const CLASSIFICATIONS = [
  'ALL', 'Potential Industrial Fire', 'Industrial Fire', 'Persistent Industrial Thermal Source',
  'Gas Flare', 'Agricultural Burning', 'Wildfire', 'Mining Activity', 'Unknown / Insufficient Evidence',
];

const STATES = ['ALL', 'West Bengal', 'Gujarat', 'Maharashtra', 'Madhya Pradesh', 'Odisha', 'Manipur', 'Bihar', 'Andhra Pradesh', 'Telangana', 'Tamil Nadu', 'Punjab'];

export default function Events() {
  const navigate = useNavigate();
  const { filters, setFilter, resetFilters, filteredEvents, eventsLoading, eventsError } = useAppStore();
  const events = filteredEvents();

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#1e3a5f] flex items-center justify-between flex-shrink-0">
        <div>
          <div className="font-display font-700 text-xl tracking-[0.1em] text-[#e2eaf5]">THERMAL EVENTS</div>
          <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest">
            {events.length.toLocaleString()} EVENTS MATCHING CURRENT FILTERS
          </div>
        </div>
        <button onClick={resetFilters} className="flex items-center gap-1.5 text-[#3d6490] hover:text-[#7a9cc4] text-xs font-mono-data">
          <X size={12} /> RESET FILTERS
        </button>
      </div>

      {eventsError && <div className="px-5 py-2 border-b border-amber-800/40 bg-amber-950/20 font-mono-data text-[10px] text-amber-400">BACKEND UNAVAILABLE · DEMO DATA ACTIVE</div>}

      {/* Filters */}
      <div className="flex items-center gap-3 px-5 py-2.5 border-b border-[#1e3a5f] bg-[#050a14] flex-shrink-0 flex-wrap">
        <Filter size={12} className="text-[#3d6490] flex-shrink-0" />

        <select value={filters.riskLevel}
          onChange={(e) => setFilter('riskLevel', e.target.value)}
          className="bg-[#0a1628] border border-[#1e3a5f] text-[#7a9cc4] text-xs font-mono-data px-2 py-1 focus:outline-none focus:border-cyan-500/50">
          <option value="ALL">All Risk Levels</option>
          {(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as RiskLevel[]).map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>

        <select value={filters.classification}
          onChange={(e) => setFilter('classification', e.target.value)}
          className="bg-[#0a1628] border border-[#1e3a5f] text-[#7a9cc4] text-xs font-mono-data px-2 py-1 focus:outline-none focus:border-cyan-500/50">
          {CLASSIFICATIONS.map((c) => <option key={c} value={c}>{c === 'ALL' ? 'All Classifications' : c}</option>)}
        </select>

        <select value={filters.state}
          onChange={(e) => setFilter('state', e.target.value)}
          className="bg-[#0a1628] border border-[#1e3a5f] text-[#7a9cc4] text-xs font-mono-data px-2 py-1 focus:outline-none focus:border-cyan-500/50">
          {STATES.map((s) => <option key={s} value={s}>{s === 'ALL' ? 'All States' : s}</option>)}
        </select>

        <div className="relative">
          <Search size={11} className="absolute left-2 top-1/2 -translate-y-1/2 text-[#3d6490]" />
          <input value={filters.search} onChange={(e) => setFilter('search', e.target.value)}
            placeholder="Search ID, facility, state..."
            className="bg-[#0a1628] border border-[#1e3a5f] text-[#e2eaf5] placeholder-[#3d6490] text-xs pl-6 pr-3 py-1 font-mono-data focus:outline-none focus:border-cyan-500/50 w-48" />
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {eventsLoading && <div className="px-5 py-3 font-mono-data text-[10px] text-cyan-400">SYNCING THERMAL EVENTS...</div>}
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 z-10 bg-[#050a14]">
            <tr className="border-b border-[#1e3a5f]">
              {['EVENT ID', 'CLASSIFICATION', 'RISK', 'SCORE', 'STATE', 'DETECTED', 'SATELLITE', 'FACILITY', 'CONFIDENCE', 'ACTION'].map((h) => (
                <th key={h} className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest font-medium whitespace-nowrap border-r border-[#0d1f3c] last:border-r-0">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {events.map((evt) => (
              <tr key={evt.eventId}
                className="data-row border-b border-[#0d1f3c] cursor-pointer"
                onClick={() => navigate(`/events/${evt.eventId}`)}>
                <td className="px-3 py-2.5 font-mono-data text-cyan-400 text-[10px] whitespace-nowrap">{evt.eventId}</td>
                <td className="px-3 py-2.5 font-display font-500 text-[#e2eaf5] text-[11px] whitespace-nowrap">{evt.classification}</td>
                <td className="px-3 py-2.5 whitespace-nowrap"><RiskBadge level={evt.riskLevel} size="sm" /></td>
                <td className="px-3 py-2.5 font-mono-data text-[#7a9cc4] text-[10px]">{evt.riskScore}</td>
                <td className="px-3 py-2.5 font-mono-data text-[#7a9cc4] text-[10px] whitespace-nowrap">{evt.state}</td>
                <td className="px-3 py-2.5 font-mono-data text-[#3d6490] text-[10px] whitespace-nowrap">{evt.acquisitionDate}</td>
                <td className="px-3 py-2.5 font-mono-data text-[#3d6490] text-[10px]">{evt.satellite}</td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] text-[#7a9cc4] whitespace-nowrap max-w-[140px] truncate">
                  {evt.facilityName ?? '—'}
                </td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] text-[#7a9cc4]">{evt.confidence}%</td>
                <td className="px-3 py-2.5 font-mono-data text-[10px]">
                  <span className={`tracking-wide ${
                    evt.recommendedAction.includes('Immediate') ? 'text-red-400' :
                    evt.recommendedAction.includes('Verify') ? 'text-orange-400' :
                    evt.recommendedAction.includes('Monitor') ? 'text-amber-400' : 'text-green-400'
                  }`}>
                    {evt.recommendedAction.split(' ').slice(0, 2).join(' ')}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!eventsLoading && events.length === 0 && <div className="p-6 text-center font-mono-data text-xs text-[#3d6490]">NO EVENTS MATCH CURRENT FILTERS</div>}
      </div>
    </div>
  );
}

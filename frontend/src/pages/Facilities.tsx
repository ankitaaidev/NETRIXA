import { useEffect, useState } from 'react';
import { Building2 } from 'lucide-react';
import { FACILITIES } from '../data/mockData';
import { api } from '../services/api';
import type { Facility } from '../types';

const STATUS_COLOR: Record<string, string> = {
  NORMAL: '#22c55e',
  WATCH: '#f59e0b',
  ABNORMAL: '#f97316',
  CRITICAL: '#ef4444',
};

export default function Facilities() {
  const [selected, setSelected] = useState<string | null>(null);
  const [facilities, setFacilities] = useState<Facility[]>(FACILITIES);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    void api.getFacilities().then((nextFacilities) => {
      if (active) { setFacilities(nextFacilities); setLoading(false); }
    }).catch(() => {
      if (active) { setError(true); setLoading(false); }
    });
    return () => { active = false; };
  }, []);

  const facility = facilities.find((f) => f.facilityId === selected);

  return (
    <div className="flex h-full">
      {/* Table */}
      <div className={`flex flex-col ${selected ? 'w-2/3' : 'flex-1'} border-r border-[#1e3a5f] overflow-auto transition-all`}>
        <div className="px-5 py-4 border-b border-[#1e3a5f] flex-shrink-0">
          <div className="font-display font-700 text-xl tracking-[0.1em] text-[#e2eaf5]">INDUSTRIAL FACILITIES</div>
          <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest">{facilities.length} REGISTERED FACILITIES · INDIA</div>
        </div>
        {error && <div className="px-5 py-2 font-mono-data text-[10px] text-amber-400">BACKEND UNAVAILABLE · DEMO DATA ACTIVE</div>}
        {loading && <div className="px-5 py-2 font-mono-data text-[10px] text-cyan-400">SYNCING FACILITIES...</div>}
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#050a14] z-10">
            <tr className="border-b border-[#1e3a5f]">
              {['FACILITY', 'TYPE', 'STATE', 'STATUS', '30D ACTIVITY', '90D ACTIVITY', 'NEARBY EVENTS', 'LAST DETECTION'].map((h) => (
                <th key={h} className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {facilities.map((f) => (
              <tr key={f.facilityId}
                className={`data-row border-b border-[#0d1f3c] cursor-pointer ${selected === f.facilityId ? 'bg-cyan-500/5' : ''}`}
                onClick={() => setSelected(selected === f.facilityId ? null : f.facilityId)}>
                <td className="px-3 py-2.5 font-display font-500 text-[11px] text-[#e2eaf5] whitespace-nowrap">{f.name}</td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] text-[#7a9cc4] whitespace-nowrap">{f.facilityType}</td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] text-[#7a9cc4] whitespace-nowrap">{f.state}</td>
                <td className="px-3 py-2.5">
                  <span className="flex items-center gap-1.5 font-mono-data text-[10px] tracking-widest" style={{ color: STATUS_COLOR[f.status] }}>
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: STATUS_COLOR[f.status] }} />
                    {f.status}
                  </span>
                </td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] text-[#7a9cc4]">{f.thermalActivity30d} events</td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] text-[#7a9cc4]">{f.thermalActivity90d} events</td>
                <td className="px-3 py-2.5 font-mono-data text-[10px]">
                  <span className={f.nearbyEvents > 3 ? 'text-orange-400' : 'text-[#7a9cc4]'}>{f.nearbyEvents}</span>
                </td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] text-[#3d6490]">{f.lastActivity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail panel */}
      {facility && (
        <div className="w-1/3 overflow-auto bg-[#050a14]">
          <div className="p-4 border-b border-[#1e3a5f]" style={{ borderTopColor: STATUS_COLOR[facility.status], borderTopWidth: 2 }}>
            <div className="flex items-start gap-2 mb-1">
              <Building2 size={14} className="text-[#3d6490] mt-0.5" />
              <div>
                <div className="font-display font-700 text-sm text-[#e2eaf5]">{facility.name}</div>
                <div className="font-mono-data text-[10px] text-[#3d6490]">{facility.facilityId}</div>
              </div>
            </div>
            <div className="mt-2 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full" style={{ background: STATUS_COLOR[facility.status] }} />
              <span className="font-mono-data text-[10px] tracking-widest" style={{ color: STATUS_COLOR[facility.status] }}>
                CURRENT STATUS: {facility.status}
              </span>
            </div>
          </div>

          <div className="p-4 space-y-4">
            {/* Details */}
            <div className="space-y-1.5">
              {[
                ['Type', facility.facilityType],
                ['State', facility.state],
                ['District', facility.district],
                ['Coordinates', `${facility.latitude.toFixed(4)}°N, ${facility.longitude.toFixed(4)}°E`],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-[#0d1f3c] pb-1.5">
                  <span className="font-mono-data text-[9px] text-[#3d6490]">{k}</span>
                  <span className="font-mono-data text-[10px] text-[#7a9cc4]">{v}</span>
                </div>
              ))}
            </div>

            {/* Thermal profile */}
            <div>
              <div className="font-mono-data text-[9px] text-[#3d6490] tracking-widest mb-2">THERMAL PROFILE</div>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { label: '30-Day Activity', value: `${facility.thermalActivity30d} events` },
                  { label: '90-Day Activity', value: `${facility.thermalActivity90d} events` },
                  { label: 'Nearby Events', value: `${facility.nearbyEvents} flagged` },
                  { label: 'Last Detection', value: facility.lastActivity },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-[#0a1628] border border-[#122035] p-2">
                    <div className="font-mono-data text-[8px] text-[#3d6490] mb-0.5">{label}</div>
                    <div className="font-display font-600 text-xs text-[#e2eaf5]">{value}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Status guide */}
            <div>
              <div className="font-mono-data text-[9px] text-[#3d6490] tracking-widest mb-2">CURRENT STATUS INTERPRETATION</div>
              <div className="bg-[#0a1628] border p-3" style={{ borderColor: STATUS_COLOR[facility.status] + '40' }}>
                <div className="font-display font-600 text-sm mb-1" style={{ color: STATUS_COLOR[facility.status] }}>
                  {facility.status}
                </div>
                <div className="font-mono-data text-[9px] text-[#3d6490]">
                  {facility.status === 'NORMAL' && 'Thermal activity within expected operational range. No action required.'}
                  {facility.status === 'WATCH' && 'Slightly elevated activity. Enhanced monitoring recommended.'}
                  {facility.status === 'ABNORMAL' && 'Thermal activity deviating from baseline. Verification required.'}
                  {facility.status === 'CRITICAL' && 'Significant thermal anomaly detected. Immediate investigation required.'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

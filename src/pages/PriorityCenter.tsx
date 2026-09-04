import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import { ALL_EVENTS } from '../data/mockData';

const SORTED = [...ALL_EVENTS].sort((a, b) => b.riskScore - a.riskScore);

const ACTION_COLOR: Record<string, string> = {
  'Immediate': '#ef4444',
  'Verify': '#f97316',
  'Monitor': '#f59e0b',
  'Routine': '#22c55e',
  'No': '#3d6490',
  'Observe': '#22c55e',
  'Human': '#f59e0b',
};

function getActionColor(action: string) {
  const key = action.split(' ')[0];
  return ACTION_COLOR[key] ?? '#7a9cc4';
}

export default function PriorityCenter() {
  const navigate = useNavigate();
  const [sortField, setSortField] = useState<'riskScore' | 'confidence' | 'zScore'>('riskScore');
  const [sortDir, setSortDir] = useState<'desc' | 'asc'>('desc');
  const [filterRisk, setFilterRisk] = useState('ALL');

  const sorted = [...SORTED]
    .filter((e) => filterRisk === 'ALL' || e.riskLevel === filterRisk)
    .sort((a, b) => {
      const diff = (a[sortField] as number) - (b[sortField] as number);
      return sortDir === 'desc' ? -diff : diff;
    });

  const toggleSort = (field: typeof sortField) => {
    if (sortField === field) setSortDir((d) => d === 'desc' ? 'asc' : 'desc');
    else { setSortField(field); setSortDir('desc'); }
  };

  const SortIcon = ({ field }: { field: typeof sortField }) =>
    sortField === field ? (sortDir === 'desc' ? <ArrowDown size={10} /> : <ArrowUp size={10} />) : <Minus size={10} className="opacity-30" />;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#1e3a5f] flex-shrink-0">
        <div className="font-display font-700 text-xl tracking-[0.1em] text-[#e2eaf5]">PRIORITY CENTER</div>
        <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mt-0.5">
          RANKED THERMAL EVENTS REQUIRING OPERATOR ATTENTION · {sorted.length} EVENTS
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 px-5 py-2 border-b border-[#1e3a5f] flex-shrink-0">
        {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((r) => (
          <button key={r}
            onClick={() => setFilterRisk(r)}
            className={`font-mono-data text-[10px] tracking-widest px-2.5 py-1 border transition-colors ${
              filterRisk === r ? 'border-cyan-500/50 bg-cyan-500/10 text-cyan-400' : 'border-[#1e3a5f] text-[#3d6490] hover:text-[#7a9cc4]'
            }`}>
            {r}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#050a14] z-10">
            <tr className="border-b border-[#1e3a5f]">
              <th className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest w-10">#</th>
              <th className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest">EVENT</th>
              <th className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest">CLASSIFICATION</th>
              <th className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest">LOCATION</th>
              <th className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest">RISK</th>
              <th className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest cursor-pointer hover:text-[#7a9cc4]"
                onClick={() => toggleSort('riskScore')}>
                <span className="flex items-center gap-1">SCORE <SortIcon field="riskScore" /></span>
              </th>
              <th className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest cursor-pointer hover:text-[#7a9cc4]"
                onClick={() => toggleSort('confidence')}>
                <span className="flex items-center gap-1">CONFIDENCE <SortIcon field="confidence" /></span>
              </th>
              <th className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest cursor-pointer hover:text-[#7a9cc4]"
                onClick={() => toggleSort('zScore')}>
                <span className="flex items-center gap-1">DEVIATION <SortIcon field="zScore" /></span>
              </th>
              <th className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest">DETECTED</th>
              <th className="px-3 py-2.5 text-left font-mono-data text-[9px] text-[#3d6490] tracking-widest">ACTION</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((evt, idx) => (
              <tr key={evt.id}
                className="data-row border-b border-[#0d1f3c] cursor-pointer"
                onClick={() => navigate(`/events/${evt.id}`)}>
                <td className="px-3 py-2.5 font-mono-data text-[#3d6490] text-[10px]">{String(idx + 1).padStart(2, '0')}</td>
                <td className="px-3 py-2.5 font-mono-data text-cyan-400 text-[10px] whitespace-nowrap">{evt.eventId}</td>
                <td className="px-3 py-2.5 font-display font-500 text-[11px] text-[#e2eaf5] whitespace-nowrap">{evt.classification}</td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] text-[#7a9cc4] whitespace-nowrap">
                  {evt.state} · {evt.district}
                </td>
                <td className="px-3 py-2.5 whitespace-nowrap"><RiskBadge level={evt.riskLevel} size="sm" /></td>
                <td className="px-3 py-2.5 font-mono-data text-[11px] font-medium text-[#e2eaf5]">{evt.riskScore}</td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] text-[#7a9cc4]">{evt.confidence}%</td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] text-[#7a9cc4]">+{evt.zScore.toFixed(1)}σ</td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] text-[#3d6490] whitespace-nowrap">{evt.acquisitionDate}</td>
                <td className="px-3 py-2.5 font-mono-data text-[10px] whitespace-nowrap" style={{ color: getActionColor(evt.recommendedAction) }}>
                  {evt.recommendedAction.split(' ').slice(0, 2).join(' ')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

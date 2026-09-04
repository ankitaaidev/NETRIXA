import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { ALL_EVENTS } from '../data/mockData';

// Build daily counts for 30 days
const DAILY = Array.from({ length: 30 }, (_, i) => {
  const d = new Date('2026-09-04');
  d.setDate(d.getDate() - (29 - i));
  return {
    date: d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
    total: Math.round(380 + Math.random() * 80),
    industrial: Math.round(25 + Math.random() * 15),
    agricultural: Math.round(120 + Math.random() * 40),
    wildfire: Math.round(10 + Math.random() * 10),
  };
});

const CLASS_DIST = [
  { name: 'Persistent Industrial', value: 124, color: '#38bdf8' },
  { name: 'Agricultural Burning', value: 312, color: '#22c55e' },
  { name: 'Industrial Fire', value: 47, color: '#ef4444' },
  { name: 'Gas Flare', value: 98, color: '#f97316' },
  { name: 'Wildfire', value: 88, color: '#f59e0b' },
  { name: 'Mining Activity', value: 65, color: '#7a9cc4' },
  { name: 'Unknown', value: 102, color: '#3d6490' },
];

const RISK_OVER_TIME = Array.from({ length: 12 }, (_, i) => {
  const months = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'];
  return {
    month: months[i],
    critical: Math.round(5 + Math.random() * 10),
    high: Math.round(20 + Math.random() * 20),
    medium: Math.round(80 + Math.random() * 40),
    low: Math.round(200 + Math.random() * 100),
  };
});

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
  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#1e3a5f] flex-shrink-0">
        <div className="font-display font-700 text-xl tracking-[0.1em] text-[#e2eaf5]">HISTORICAL INTELLIGENCE</div>
        <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest">THERMAL EVENT PATTERNS · INDIA · OCT 2025 – SEP 2026</div>
      </div>

      <div className="p-5 space-y-4">
        {/* Daily events */}
        <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
          <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">30-DAY DAILY EVENT VOLUME</div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={DAILY} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
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
                <Pie data={CLASS_DIST} dataKey="value" cx={75} cy={75} outerRadius={70} innerRadius={40} strokeWidth={0}>
                  {CLASS_DIST.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
              <div className="flex-1 space-y-1.5">
                {CLASS_DIST.map(({ name, value, color }) => (
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
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={RISK_OVER_TIME} margin={{ top: 5, right: 10, left: -20, bottom: 0 }} stackOffset="none">
                <CartesianGrid strokeDasharray="2 4" stroke="#1e3a5f" strokeOpacity={0.3} />
                <XAxis dataKey="month" tick={{ fontSize: 8, fill: '#3d6490', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 8, fill: '#3d6490', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="critical" name="Critical" stackId="a" fill="#ef4444" opacity={0.8} />
                <Bar dataKey="high" name="High" stackId="a" fill="#f97316" opacity={0.8} />
                <Bar dataKey="medium" name="Medium" stackId="a" fill="#f59e0b" opacity={0.8} />
                <Bar dataKey="low" name="Low" stackId="a" fill="#22c55e" opacity={0.5} />
              </BarChart>
            </ResponsiveContainer>
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
              {[
                ['Paradip Refinery', 'Odisha', 'Gas Flare', 201, '385 K', 'NORMAL'],
                ['Ramagundam TPP', 'Telangana', 'Power Plant', 178, '345 K', 'NORMAL'],
                ['Hazira LNG', 'Gujarat', 'LNG Terminal', 142, '341 K', 'NORMAL'],
                ['Jamnagar Refinery', 'Gujarat', 'Refinery', 138, '362 K', 'NORMAL'],
                ['Rourkela Steel', 'Odisha', 'Steel Plant', 112, '358 K', 'WATCH'],
                ['NTPC Vindhyachal', 'M.P.', 'Power Plant', 108, '344 K', 'NORMAL'],
                ['Haldia Petrochems', 'W. Bengal', 'Petrochemical', 94, '352 K', 'NORMAL'],
                ['IOCL Panipat', 'Haryana', 'Refinery', 87, '371 K', 'WATCH'],
                ['Vizag Steel', 'A.P.', 'Steel Plant', 82, '355 K', 'NORMAL'],
                ['HPCL Vizag', 'A.P.', 'Refinery', 74, '363 K', 'ABNORMAL'],
              ].map(([loc, state, type, obs, mean, status]) => (
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

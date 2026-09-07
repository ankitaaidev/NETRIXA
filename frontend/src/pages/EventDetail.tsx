import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, MapPin, Satellite, Clock, Building2, Layers,
  CheckCircle, AlertCircle, BarChart2, Brain, History, Info,
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, ReferenceLine, Cell,
} from 'recharts';
import RiskBadge from '../components/RiskBadge';
import { ALL_EVENTS } from '../data/mockData';
import { api } from '../services/api';
import type { ThermalEvent } from '../types';

type Tab = 'overview' | 'thermal' | 'history' | 'satellite' | 'ai' | 'explanation';

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: 'overview', label: 'Overview', icon: Info },
  { id: 'thermal', label: 'Thermal Analysis', icon: BarChart2 },
  { id: 'history', label: 'Historical Behaviour', icon: History },
  { id: 'satellite', label: 'Satellite Evidence', icon: Satellite },
  { id: 'ai', label: 'AI Classification', icon: Brain },
  { id: 'explanation', label: 'AI Explanation', icon: CheckCircle },
];

const FACTOR_COLORS: Record<string, string> = {
  HIGH: '#f97316',
  MEDIUM: '#f59e0b',
  LOW: '#22c55e',
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass px-3 py-2">
      <div className="font-mono-data text-[9px] text-[#7a9cc4] mb-1">{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} className="font-mono-data text-[10px]" style={{ color: p.color }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
        </div>
      ))}
    </div>
  );
};

export default function EventDetail() {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>('overview');
  const [feedback, setFeedback] = useState<string | null>(null);
  const [event, setEvent] = useState<ThermalEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    const fallback = ALL_EVENTS.find((candidate) => candidate.eventId === eventId);
    void api.getEvent(eventId || '').then((nextEvent) => {
      if (active) { setEvent(nextEvent); setLoading(false); }
    }).catch((requestError) => {
      if (!active) return;
      if (fallback) {
        setEvent({ ...fallback, id: fallback.eventId });
        setError('BACKEND UNAVAILABLE · DEMO DATA ACTIVE');
      } else {
        setEvent(null);
        setError(requestError instanceof Error ? requestError.message : 'Event could not be loaded.');
      }
      setLoading(false);
    });
    return () => { active = false; };
  }, [eventId]);

  const submitFeedback = (label: string) => {
    setFeedback(label);
    if (!event) return;
    const decision = label === 'Confirmed' ? 'CONFIRMED' : label === 'False Positive' ? 'FALSE_POSITIVE' : label === 'Needs Investigation' ? 'NEEDS_REVIEW' : null;
    if (decision) void api.submitFeedback(event.eventId, decision).catch(() => setError('FEEDBACK COULD NOT BE RECORDED'));
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full text-cyan-400 font-mono-data text-sm">LOADING EVENT INVESTIGATION...</div>;
  }
  if (!event) {
    return (
      <div className="flex items-center justify-center h-full text-[#3d6490] font-mono-data text-sm">
        EVENT NOT FOUND · {error}
      </div>
    );
  }

  const riskColor =
    event.riskLevel === 'CRITICAL' ? '#ef4444' :
    event.riskLevel === 'HIGH' ? '#f97316' :
    event.riskLevel === 'MEDIUM' ? '#f59e0b' : '#22c55e';

  const topProb = Object.entries(event.classificationProbabilities).sort((a, b) => b[1] - a[1]);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {error && <div className="px-5 py-2 border-b border-amber-800/40 bg-amber-950/20 font-mono-data text-[10px] text-amber-400">{error}</div>}
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#1e3a5f] flex-shrink-0"
        style={{ borderTopColor: riskColor, borderTopWidth: 2 }}>
        <button onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-[#3d6490] hover:text-[#7a9cc4] text-xs font-mono-data mb-3 transition-colors">
          <ArrowLeft size={12} /> BACK TO EVENTS
        </button>
        <div className="flex items-start justify-between">
          <div>
            <div className="font-mono-data text-[11px] text-[#7a9cc4] tracking-widest">{event.eventId}</div>
            <div className="font-display font-700 text-2xl tracking-wide text-[#e2eaf5] mt-1">{event.classification}</div>
            <div className="flex items-center gap-3 mt-2">
              <RiskBadge level={event.riskLevel} pulse size="md" />
              <span className="font-mono-data text-xs text-[#7a9cc4]">Risk Score: {event.riskScore} / 100</span>
              <span className="font-mono-data text-xs text-[#7a9cc4]">Confidence: {event.confidence}%</span>
            </div>
          </div>
          {/* Quick meta */}
          <div className="hidden lg:grid grid-cols-2 gap-x-6 gap-y-1.5 text-right">
            {[
              [MapPin, `${event.latitude.toFixed(4)}°N, ${event.longitude.toFixed(4)}°E`],
              [Clock, `${event.acquisitionDate} · ${event.acquisitionTime}`],
              [Satellite, `${event.satellite} / ${event.instrument}`],
              [Layers, event.landCover],
            ].map(([Icon, val], i) => (
              <div key={i} className="flex items-center gap-1.5 justify-end">
                {/* @ts-ignore */}
                <Icon size={11} className="text-[#3d6490]" />
                <span className="font-mono-data text-[10px] text-[#7a9cc4]">{val as string}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#1e3a5f] flex-shrink-0 bg-[#050a14]">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 font-display font-600 text-xs tracking-wider transition-colors relative ${
              tab === id ? 'tab-active text-cyan-400' : 'text-[#3d6490] hover:text-[#7a9cc4]'
            }`}>
            <Icon size={12} />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-5">
        {/* OVERVIEW */}
        {tab === 'overview' && (
          <div className="grid grid-cols-3 gap-4">
            {/* Left: summary cards */}
            <div className="col-span-2 space-y-4">
              {/* Event summary */}
              <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
                <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">EVENT SUMMARY</div>
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { label: 'Classification', value: event.classification, color: '#e2eaf5' },
                    { label: 'Confidence', value: `${event.confidence}%`, color: '#38bdf8' },
                    { label: 'Risk Score', value: `${event.riskScore} / 100`, color: riskColor },
                    { label: 'Thermal Intensity', value: `${event.brightnessTemperature} K`, color: '#f97316' },
                    { label: 'FRP', value: `${event.frp} MW`, color: '#f97316' },
                    { label: 'Persistence', value: event.observations + ' observations', color: '#38bdf8' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-[#050a14] border border-[#122035] p-3">
                      <div className="font-mono-data text-[9px] text-[#3d6490] tracking-wide mb-1">{label}</div>
                      <div className="font-display font-600 text-sm" style={{ color }}>{value}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Metadata */}
              <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
                <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">DETECTION METADATA</div>
                <div className="grid grid-cols-2 gap-y-2 gap-x-8">
                  {[
                    ['Coordinates', `${event.latitude.toFixed(4)}°N, ${event.longitude.toFixed(4)}°E`],
                    ['Detection Time', `${event.acquisitionDate} · ${event.acquisitionTime}`],
                    ['Satellite', event.satellite],
                    ['Instrument', event.instrument],
                    ['Land Cover', event.landCover],
                    ['State / District', `${event.state} · ${event.district}`],
                    ...(event.facilityName ? [
                      ['Nearest Facility', event.facilityName],
                      ['Facility Distance', `${event.facilityDistance} m`],
                      ['Facility Type', event.facilityType!],
                    ] : []),
                  ].map(([k, v]) => (
                    <div key={k} className="flex items-baseline gap-2 border-b border-[#0d1f3c] pb-1.5">
                      <span className="font-mono-data text-[10px] text-[#3d6490] tracking-wide w-36 flex-shrink-0">{k}</span>
                      <span className="font-mono-data text-[10px] text-[#7a9cc4]">{v as string}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right panel */}
            <div className="space-y-4">
              {/* Risk breakdown */}
              <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
                <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">RISK FACTORS</div>
                {[
                  { label: 'Thermal Anomaly', score: Math.round(event.anomalyScore * 100), weight: '30%' },
                  { label: 'Industrial Proximity', score: event.industrialProximity === 'HIGH' ? 90 : event.industrialProximity === 'MEDIUM' ? 55 : 15, weight: '20%' },
                  { label: 'Historical Deviation', score: Math.min(100, Math.round(event.zScore * 28)), weight: '15%' },
                  { label: 'Spatial Change', score: event.spatialChange === 'HIGH' ? 85 : event.spatialChange === 'MEDIUM' ? 50 : 15, weight: '15%' },
                  { label: 'Persistence', score: event.persistence === 'ABNORMAL_PERSISTENT' ? 80 : event.persistence === 'SUDDEN_EVENT' ? 70 : 20, weight: '10%' },
                  { label: 'Classification Conf.', score: event.confidence, weight: '10%' },
                ].map(({ label, score, weight }) => (
                  <div key={label} className="mb-2.5">
                    <div className="flex justify-between mb-1">
                      <span className="font-mono-data text-[9px] text-[#7a9cc4]">{label}</span>
                      <span className="font-mono-data text-[9px] text-[#3d6490]">{weight} · {score}</span>
                    </div>
                    <div className="h-1 bg-[#050a14]">
                      <div className="h-full" style={{
                        width: `${score}%`,
                        background: score >= 75 ? '#ef4444' : score >= 50 ? '#f97316' : score >= 25 ? '#f59e0b' : '#22c55e',
                        opacity: 0.8,
                      }} />
                    </div>
                  </div>
                ))}
                <div className="mt-3 pt-2 border-t border-[#122035] flex justify-between">
                  <span className="font-mono-data text-[10px] text-[#3d6490] tracking-wide">COMPOSITE RISK SCORE</span>
                  <span className="font-display font-700 text-lg" style={{ color: riskColor }}>{event.riskScore}</span>
                </div>
                <p className="font-mono-data text-[9px] text-[#3d6490] mt-1">* Prototype scoring — weights configurable · Not scientifically validated</p>
              </div>

              {/* Recommended action */}
              <div className="bg-[#0a1628] border p-4" style={{ borderColor: riskColor + '40' }}>
                <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-2">RECOMMENDED ACTION</div>
                <div className="font-display font-600 text-sm" style={{ color: riskColor }}>{event.recommendedAction}</div>
              </div>

              {/* Analyst feedback */}
              <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
                <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-2">ANALYST FEEDBACK</div>
                <div className="grid grid-cols-2 gap-1.5">
                  {['Confirmed', 'False Positive', 'Needs Investigation', 'Unknown'].map((f) => (
                    <button key={f}
                      onClick={() => submitFeedback(f)}
                      className={`py-1.5 text-[10px] font-mono-data tracking-wide border transition-colors ${
                        feedback === f
                          ? 'border-cyan-500/50 bg-cyan-500/10 text-cyan-400'
                          : 'border-[#1e3a5f] text-[#3d6490] hover:border-[#2d5a8e] hover:text-[#7a9cc4]'
                      }`}>{f}</button>
                  ))}
                </div>
                {feedback && (
                  <div className="mt-2 font-mono-data text-[9px] text-green-400">✓ FEEDBACK RECORDED: {feedback.toUpperCase()}</div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* THERMAL ANALYSIS */}
        {tab === 'thermal' && (
          <div className="space-y-4">
            <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
              <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-4">THERMAL INTENSITY PROFILE — 90 DAYS</div>
              <div className="grid grid-cols-3 gap-4 mb-4">
                {[
                  { label: 'Historical Baseline', value: event.historicalMean.toFixed(1), unit: 'K mean' },
                  { label: 'Current Observation', value: event.brightnessTemperature.toString(), unit: 'K brightness', highlight: true },
                  { label: 'Deviation', value: `+${event.zScore.toFixed(1)}σ`, unit: 'z-score', warn: event.zScore > 2 },
                ].map(({ label, value, unit, highlight, warn }) => (
                  <div key={label} className="bg-[#050a14] border border-[#122035] p-3">
                    <div className="font-mono-data text-[9px] text-[#3d6490] mb-1 tracking-wide">{label}</div>
                    <div className={`font-display font-700 text-2xl ${highlight ? 'text-orange-400' : warn ? 'text-amber-400' : 'text-[#e2eaf5]'}`}>{value}</div>
                    <div className="font-mono-data text-[9px] text-[#3d6490]">{unit}</div>
                  </div>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={event.historicalData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="tGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="2 4" stroke="#1e3a5f" strokeOpacity={0.3} />
                  <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#3d6490', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} interval={14} />
                  <YAxis tick={{ fontSize: 9, fill: '#3d6490', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine y={event.historicalMean} stroke="#38bdf8" strokeDasharray="4 4" strokeWidth={1} label={{ value: 'Baseline', fill: '#38bdf8', fontSize: 9 }} />
                  <ReferenceLine y={event.historicalMean + 2 * event.historicalStd} stroke="#f59e0b" strokeDasharray="3 5" strokeWidth={0.8} label={{ value: 'Threshold', fill: '#f59e0b', fontSize: 9 }} />
                  <Area type="monotone" dataKey="intensity" name="Intensity (K)" stroke="#38bdf8" strokeWidth={1.5} fill="url(#tGrad)" dot={(props) => {
                    const { cx, cy, payload } = props;
                    if (payload.isAnomaly) return <circle key={cx} cx={cx} cy={cy} r={5} fill="#ef4444" stroke="#fff" strokeWidth={1} />;
                    return <></>;
                  }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* HISTORICAL BEHAVIOUR */}
        {tab === 'history' && (
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2 bg-[#0a1628] border border-[#1e3a5f] p-4">
              <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-4">HISTORICAL THERMAL ACTIVITY</div>
              <div className="grid grid-cols-3 gap-3 mb-4">
                {[
                  { label: 'Historical Mean', value: event.historicalMean.toFixed(0) },
                  { label: 'Current Intensity', value: event.brightnessTemperature.toString() },
                  { label: 'Deviation', value: `+${event.zScore.toFixed(1)}σ` },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-[#050a14] border border-[#122035] p-3 text-center">
                    <div className="font-mono-data text-[9px] text-[#3d6490] mb-1">{label}</div>
                    <div className="font-display font-700 text-xl text-[#e2eaf5]">{value}</div>
                  </div>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={event.historicalData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="hGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#7a9cc4" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#7a9cc4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="2 4" stroke="#1e3a5f" strokeOpacity={0.3} />
                  <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#3d6490', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} interval={14} />
                  <YAxis tick={{ fontSize: 9, fill: '#3d6490', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine y={event.historicalMean} stroke="#7a9cc4" strokeDasharray="4 4" strokeWidth={1} />
                  <ReferenceLine y={event.historicalMean + 2 * event.historicalStd} stroke="#f59e0b" strokeDasharray="3 5" strokeWidth={0.8} />
                  <Area type="monotone" dataKey="intensity" name="Intensity (K)" stroke="#7a9cc4" strokeWidth={1.5} fill="url(#hGrad)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
              <p className="font-mono-data text-[9px] text-[#3d6490] mt-2">* DEMO: Historical data is simulated for prototype demonstration</p>
            </div>

            <div className="space-y-3">
              <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
                <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">PERSISTENCE ANALYSIS</div>
                <div className="space-y-2">
                  {[
                    ['First Observed', event.firstObserved],
                    ['Last Observed', event.lastObserved],
                    ['Total Observations', event.observations.toString()],
                    ['Recurrence', event.observations > 10 ? 'High' : event.observations > 3 ? 'Medium' : 'Low'],
                    ['Spatial Stability', event.spatialChange === 'STABLE' ? 'High' : event.spatialChange === 'LOW' ? 'Medium' : 'Low'],
                  ].map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b border-[#0d1f3c] pb-1.5">
                      <span className="font-mono-data text-[9px] text-[#3d6490]">{k}</span>
                      <span className="font-mono-data text-[10px] text-[#7a9cc4]">{v as string}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-3 pt-2 border-t border-[#122035]">
                  <div className="font-mono-data text-[9px] text-[#3d6490] mb-1">BEHAVIOUR CLASSIFICATION</div>
                  <div className={`font-display font-600 text-sm ${
                    event.persistence === 'ABNORMAL_PERSISTENT' ? 'text-orange-400' :
                    event.persistence === 'SUDDEN_EVENT' ? 'text-red-400' :
                    event.persistence === 'NORMAL_PERSISTENT' ? 'text-green-400' :
                    event.persistence === 'INTERMITTENT' ? 'text-amber-400' : 'text-[#7a9cc4]'
                  }`}>{event.persistence.replace(/_/g, ' ')}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* SATELLITE EVIDENCE */}
        {tab === 'satellite' && (
          <div className="space-y-4">
            <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
              <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">SATELLITE DETECTION RECORD</div>
              <div className="grid grid-cols-3 gap-4 mb-4">
                {[['Satellite', event.satellite], ['Instrument', event.instrument], ['Acquisition', event.acquisitionDate]].map(([k, v]) => (
                  <div key={k} className="bg-[#050a14] border border-[#122035] p-3">
                    <div className="font-mono-data text-[9px] text-[#3d6490] mb-1">{k}</div>
                    <div className="font-display font-600 text-sm text-[#e2eaf5]">{v as string}</div>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-4">
                {['Pre-Event Imagery', 'Event Imagery'].map((label) => (
                  <div key={label} className="border border-[#1e3a5f] bg-[#050a14] aspect-video flex items-center justify-center">
                    <div className="text-center">
                      <Satellite size={24} className="text-[#1e3a5f] mx-auto mb-2" />
                      <div className="font-mono-data text-[10px] text-[#3d6490]">{label}</div>
                      <div className="font-mono-data text-[9px] text-[#3d6490] mt-1">Satellite evidence unavailable in demo mode</div>
                    </div>
                  </div>
                ))}
              </div>
              <p className="font-mono-data text-[9px] text-[#3d6490] mt-3">* Live satellite imagery requires FIRMS / Sentinel API integration. Architecture is ready for real data connection.</p>
            </div>
          </div>
        )}

        {/* AI CLASSIFICATION */}
        {tab === 'ai' && (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
              <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-4">AI SOURCE CLASSIFICATION</div>
              <p className="font-mono-data text-[9px] text-[#3d6490] mb-4">* PROTOTYPE MODEL — Classification probabilities are illustrative. Not production-validated.</p>
              <div className="space-y-3">
                {topProb.map(([cls, prob]) => (
                  <div key={cls}>
                    <div className="flex justify-between mb-1">
                      <span className={`font-display font-600 text-xs ${cls === event.classification ? 'text-[#e2eaf5]' : 'text-[#7a9cc4]'}`}>{cls}</span>
                      <span className="font-mono-data text-[11px] text-[#7a9cc4]">{Math.round(prob * 100)}%</span>
                    </div>
                    <div className="h-1.5 bg-[#050a14]">
                      <div className="h-full transition-all" style={{
                        width: `${prob * 100}%`,
                        background: cls === event.classification ? '#38bdf8' : '#1e3a5f',
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
              <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-4">CLASSIFICATION BAR CHART</div>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={topProb.map(([cls, p]) => ({ cls: cls.slice(0, 18), prob: Math.round(p * 100) }))}
                  layout="vertical" margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="2 4" stroke="#1e3a5f" strokeOpacity={0.3} horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 9, fill: '#3d6490', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="cls" tick={{ fontSize: 9, fill: '#7a9cc4', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} width={130} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="prob" name="Probability %">
                    {topProb.map(([cls], i) => (
                      <Cell key={i} fill={cls === event.classification ? '#38bdf8' : '#1e3a5f'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* AI EXPLANATION */}
        {tab === 'explanation' && (
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2 bg-[#0a1628] border border-[#1e3a5f] p-4">
              <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-1">WHY NETRIXA FLAGGED THIS EVENT</div>
              <div className="font-display text-sm text-[#7a9cc4] mb-4">Evidence factors that contributed to classification and risk assessment</div>
              <div className="space-y-2">
                {event.explanation.map((factor) => (
                  <div key={factor.factor} className={`flex items-start gap-3 p-3 border ${
                    factor.confirmed ? 'border-[#1e3a5f] bg-[#050a14]' : 'border-[#122035] bg-[#050a14] opacity-70'
                  }`}>
                    {factor.confirmed
                      ? <CheckCircle size={14} className="text-green-400 flex-shrink-0 mt-0.5" />
                      : <AlertCircle size={14} className="text-[#3d6490] flex-shrink-0 mt-0.5" />}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="font-display font-600 text-xs text-[#e2eaf5]">{factor.factor}</span>
                        <span className="font-mono-data text-[9px] px-1.5 py-0.5 border" style={{
                          color: FACTOR_COLORS[factor.value],
                          borderColor: FACTOR_COLORS[factor.value] + '40',
                          background: FACTOR_COLORS[factor.value] + '10',
                        }}>{factor.value}</span>
                      </div>
                      <div className="font-mono-data text-[10px] text-[#3d6490]">{factor.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-3">
              <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
                <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">PRIMARY CONTRIBUTING FACTORS</div>
                {[
                  { label: 'Industrial Context', value: event.industrialProximity },
                  { label: 'Thermal Anomaly', value: event.zScore > 2.5 ? 'HIGH' : event.zScore > 1.5 ? 'MEDIUM' : 'LOW' },
                  { label: 'Historical Deviation', value: event.zScore > 2 ? 'HIGH' : event.zScore > 1 ? 'MEDIUM' : 'LOW' },
                  { label: 'Spatial Change', value: event.spatialChange },
                  { label: 'Persistence Pattern', value: event.observations > 10 ? 'HIGH' : event.observations > 3 ? 'MEDIUM' : 'LOW' },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between items-center border-b border-[#0d1f3c] py-1.5">
                    <span className="font-mono-data text-[10px] text-[#7a9cc4]">{label}</span>
                    <span className="font-mono-data text-[10px]" style={{ color: FACTOR_COLORS[value] || '#7a9cc4' }}>{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Check, Clock } from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import { ALERTS } from '../data/mockData';
import { api } from '../services/api';
import type { Alert } from '../types';

const SEV_COLOR: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#f59e0b',
  LOW: '#22c55e',
};

export default function Alerts() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<Alert[]>(ALERTS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filter, setFilter] = useState<'ALL' | 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED'>('ALL');

  useEffect(() => {
    let active = true;
    void api.getAlerts().then((nextAlerts) => {
      if (active) { setAlerts(nextAlerts); setLoading(false); }
    }).catch(() => {
      if (active) { setError(true); setLoading(false); }
    });
    return () => { active = false; };
  }, []);

  const filtered = alerts.filter((a) => filter === 'ALL' || a.status === filter);
  const active = alerts.filter((a) => a.status === 'ACTIVE').length;

  const acknowledge = (id: string) => {
    void api.resolveAlert(id).then((resolved) => {
      setAlerts((prev) => prev.map((alert) => alert.id === id ? resolved : alert));
    }).catch(() => setError(true));
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#1e3a5f] flex items-center justify-between flex-shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <div className="font-display font-700 text-xl tracking-[0.1em] text-[#e2eaf5]">ALERT CENTER</div>
            {active > 0 && (
              <span className="font-mono-data text-[10px] bg-red-500/20 border border-red-500/40 text-red-400 px-2 py-0.5">{active} ACTIVE</span>
            )}
          </div>
          <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest">PRIORITY THERMAL ANOMALY NOTIFICATIONS</div>
        </div>
      </div>
      {error && <div className="px-5 py-2 border-b border-amber-800/40 bg-amber-950/20 font-mono-data text-[10px] text-amber-400">BACKEND UNAVAILABLE · DEMO DATA ACTIVE</div>}

      {/* Filter tabs */}
      <div className="flex border-b border-[#1e3a5f] flex-shrink-0">
        {(['ALL', 'ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'] as const).map((f) => (
          <button key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2.5 font-mono-data text-[10px] tracking-widest border-r border-[#1e3a5f] transition-colors relative ${
              filter === f ? 'tab-active text-cyan-400 bg-cyan-500/5' : 'text-[#3d6490] hover:text-[#7a9cc4]'
            }`}>
            {f}
            {f !== 'ALL' && (
              <span className="ml-1.5 font-mono-data text-[9px]">
                ({alerts.filter((a) => a.status === f).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Alerts */}
      <div className="flex-1 overflow-auto p-5 space-y-3">
        {loading && <div className="font-mono-data text-[10px] text-cyan-400">SYNCING ALERTS...</div>}
        {filtered.length === 0 && (
          <div className="flex items-center justify-center h-32 text-[#3d6490] font-mono-data text-sm">
            NO ALERTS IN THIS CATEGORY
          </div>
        )}
        {filtered.map((alert) => (
          <div key={alert.id}
            className="bg-[#0a1628] border border-[#1e3a5f] relative overflow-hidden"
            style={{ borderLeftColor: SEV_COLOR[alert.severity], borderLeftWidth: 3 }}>
            {/* Status stripe */}
            {alert.status === 'RESOLVED' && (
              <div className="absolute inset-0 bg-[#050a14]/50 pointer-events-none" />
            )}
            <div className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono-data text-[9px] tracking-widest px-1.5 py-0.5 border" style={{
                      color: SEV_COLOR[alert.severity],
                      borderColor: SEV_COLOR[alert.severity] + '40',
                      background: SEV_COLOR[alert.severity] + '10',
                    }}>{alert.severity} ALERT</span>
                    <span className={`font-mono-data text-[9px] tracking-widest ${
                      alert.status === 'ACTIVE' ? 'text-red-400' :
                      alert.status === 'ACKNOWLEDGED' ? 'text-amber-400' : 'text-green-400'
                    }`}>· {alert.status}</span>
                  </div>

                  <div className="font-display font-700 text-sm text-[#e2eaf5] mb-1">{alert.title}</div>

                  <div className="flex items-center gap-2 mb-2">
                    <Bell size={10} className="text-[#3d6490]" />
                    <span className="font-mono-data text-[10px] text-cyan-400">{alert.eventId}</span>
                    <Clock size={10} className="text-[#3d6490]" />
                    <span className="font-mono-data text-[10px] text-[#3d6490]">
                      {new Date(alert.createdAt).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}
                    </span>
                  </div>

                  <p className="font-mono-data text-[10px] text-[#7a9cc4] leading-relaxed mb-2">{alert.message}</p>

                  <div className="bg-[#050a14] border border-[#122035] px-3 py-2">
                    <span className="font-mono-data text-[9px] text-[#3d6490] tracking-wide">RECOMMENDED ACTION: </span>
                    <span className="font-mono-data text-[10px]" style={{ color: SEV_COLOR[alert.severity] }}>{alert.recommendedAction}</span>
                  </div>

                  {alert.resolvedAt && (
                    <div className="mt-2 font-mono-data text-[9px] text-green-400 flex items-center gap-1">
                      <Check size={10} /> Resolved: {new Date(alert.resolvedAt).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2 flex-shrink-0">
                  <button onClick={() => navigate(`/events/${alert.eventId}`)}
                    className="bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono-data text-[9px] tracking-widest px-3 py-1.5 hover:bg-cyan-500/20 transition-colors whitespace-nowrap">
                    INVESTIGATE
                  </button>
                  {alert.status === 'ACTIVE' && (
                    <button onClick={() => acknowledge(alert.id)}
                      className="bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono-data text-[9px] tracking-widest px-3 py-1.5 hover:bg-amber-500/20 transition-colors">
                      RESOLVE
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

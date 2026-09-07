import { useState } from 'react';
import { FileText, Download, CheckCircle } from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import { ALL_EVENTS } from '../data/mockData';

export default function Reports() {
  const [selectedId, setSelectedId] = useState('');
  const [generated, setGenerated] = useState(false);
  const [generating, setGenerating] = useState(false);

  const event = ALL_EVENTS.find((e) => e.id === selectedId);

  const generate = () => {
    setGenerating(true);
    setGenerated(false);
    setTimeout(() => { setGenerating(false); setGenerated(true); }, 1200);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-5 py-4 border-b border-[#1e3a5f] flex-shrink-0">
        <div className="font-display font-700 text-xl tracking-[0.1em] text-[#e2eaf5]">INCIDENT REPORTS</div>
        <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest">GENERATE STRUCTURED INTELLIGENCE REPORTS FOR THERMAL EVENTS</div>
      </div>

      <div className="flex-1 overflow-auto p-5">
        <div className="max-w-3xl space-y-4">
          {/* Generator */}
          <div className="bg-[#0a1628] border border-[#1e3a5f] p-4">
            <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest mb-3">REPORT GENERATOR</div>
            <div className="flex items-center gap-3">
              <select value={selectedId} onChange={(e) => { setSelectedId(e.target.value); setGenerated(false); }}
                className="flex-1 bg-[#050a14] border border-[#1e3a5f] text-[#e2eaf5] text-xs font-mono-data px-3 py-2 focus:outline-none focus:border-cyan-500/50">
                <option value="">— Select Thermal Event —</option>
                {ALL_EVENTS.map((e) => (
                  <option key={e.id} value={e.id}>{e.eventId} · {e.classification} · {e.riskLevel}</option>
                ))}
              </select>
              <button
                onClick={generate}
                disabled={!selectedId || generating}
                className="bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-display font-600 text-xs tracking-widest px-4 py-2 hover:bg-cyan-500/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap">
                {generating ? 'GENERATING...' : 'GENERATE REPORT'}
              </button>
            </div>
          </div>

          {/* Report preview */}
          {generated && event && (
            <div className="bg-[#0a1628] border border-[#1e3a5f]">
              {/* Report header */}
              <div className="px-6 py-4 border-b border-[#1e3a5f] flex items-start justify-between"
                style={{ borderTopColor: event.riskLevel === 'CRITICAL' ? '#ef4444' : event.riskLevel === 'HIGH' ? '#f97316' : '#f59e0b', borderTopWidth: 2 }}>
                <div>
                  <div className="font-mono-data text-[9px] text-[#3d6490] tracking-widest mb-1">NETRIXA INTELLIGENCE REPORT</div>
                  <div className="font-display font-700 text-lg text-[#e2eaf5]">{event.eventId}</div>
                  <div className="font-display text-sm text-[#7a9cc4] mt-0.5">{event.classification}</div>
                  <div className="flex items-center gap-2 mt-2">
                    <RiskBadge level={event.riskLevel} size="sm" />
                    <span className="font-mono-data text-[10px] text-[#3d6490]">Generated: 2026-09-04 · DEMO PROTOTYPE</span>
                  </div>
                </div>
                <button className="flex items-center gap-1.5 bg-[#050a14] border border-[#1e3a5f] text-[#7a9cc4] font-mono-data text-[10px] px-3 py-2 hover:text-[#e2eaf5] transition-colors">
                  <Download size={12} />
                  DOWNLOAD PDF
                </button>
              </div>

              <div className="p-6 space-y-5 font-mono-data text-[11px]">
                {/* Event info */}
                <section>
                  <div className="text-[9px] text-[#3d6490] tracking-widest mb-2 border-b border-[#0d1f3c] pb-1">1. EVENT IDENTIFICATION</div>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-1.5">
                    {[
                      ['Event ID', event.eventId],
                      ['Classification', event.classification],
                      ['Risk Level', event.riskLevel],
                      ['Risk Score', `${event.riskScore} / 100`],
                      ['Detection Confidence', `${event.confidence}%`],
                      ['Coordinates', `${event.latitude.toFixed(4)}°N, ${event.longitude.toFixed(4)}°E`],
                      ['Detection Time', `${event.acquisitionDate} · ${event.acquisitionTime}`],
                      ['Satellite / Instrument', `${event.satellite} / ${event.instrument}`],
                    ].map(([k, v]) => (
                      <div key={k} className="flex gap-2">
                        <span className="text-[#3d6490] w-40 flex-shrink-0">{k}:</span>
                        <span className="text-[#7a9cc4]">{v as string}</span>
                      </div>
                    ))}
                  </div>
                </section>

                {/* Thermal analysis */}
                <section>
                  <div className="text-[9px] text-[#3d6490] tracking-widest mb-2 border-b border-[#0d1f3c] pb-1">2. THERMAL ANALYSIS</div>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-1.5">
                    {[
                      ['Brightness Temperature', `${event.brightnessTemperature} K`],
                      ['Fire Radiative Power', `${event.frp} MW`],
                      ['Historical Mean', `${event.historicalMean} K`],
                      ['z-Score Deviation', `+${event.zScore.toFixed(2)}σ`],
                      ['Land Cover', event.landCover],
                      ['Anomaly Score', `${(event.anomalyScore * 100).toFixed(0)} / 100`],
                    ].map(([k, v]) => (
                      <div key={k} className="flex gap-2">
                        <span className="text-[#3d6490] w-40 flex-shrink-0">{k}:</span>
                        <span className="text-[#7a9cc4]">{v as string}</span>
                      </div>
                    ))}
                  </div>
                </section>

                {/* Facility info */}
                {event.facilityName && (
                  <section>
                    <div className="text-[9px] text-[#3d6490] tracking-widest mb-2 border-b border-[#0d1f3c] pb-1">3. FACILITY INFORMATION</div>
                    <div className="grid grid-cols-2 gap-x-8 gap-y-1.5">
                      {[
                        ['Facility Name', event.facilityName],
                        ['Facility Type', event.facilityType ?? '—'],
                        ['Distance', `${event.facilityDistance} m`],
                        ['Industrial Proximity', event.industrialProximity],
                      ].map(([k, v]) => (
                        <div key={k} className="flex gap-2">
                          <span className="text-[#3d6490] w-40 flex-shrink-0">{k}:</span>
                          <span className="text-[#7a9cc4]">{v as string}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* AI explanation */}
                <section>
                  <div className="text-[9px] text-[#3d6490] tracking-widest mb-2 border-b border-[#0d1f3c] pb-1">4. AI CLASSIFICATION EXPLANATION</div>
                  <div className="space-y-1">
                    {event.explanation.filter((f) => f.confirmed).map((f) => (
                      <div key={f.factor} className="flex items-start gap-2">
                        <CheckCircle size={10} className="text-green-400 mt-0.5 flex-shrink-0" />
                        <span className="text-[#7a9cc4]">{f.factor}: {f.description}</span>
                      </div>
                    ))}
                  </div>
                  <p className="mt-2 text-[9px] text-[#3d6490]">* PROTOTYPE — Classification is indicative. Not production-validated. Model output intended for human review.</p>
                </section>

                {/* Recommended action */}
                <section>
                  <div className="text-[9px] text-[#3d6490] tracking-widest mb-2 border-b border-[#0d1f3c] pb-1">5. RECOMMENDED ACTION</div>
                  <div className="bg-[#050a14] border px-3 py-2" style={{ borderColor: event.riskLevel === 'CRITICAL' ? '#ef444440' : '#1e3a5f' }}>
                    <span className={`text-sm font-bold ${
                      event.riskLevel === 'CRITICAL' ? 'text-red-400' :
                      event.riskLevel === 'HIGH' ? 'text-orange-400' : 'text-amber-400'
                    }`}>{event.recommendedAction}</span>
                  </div>
                </section>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

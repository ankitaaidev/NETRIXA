export default function Settings() {
  return (
    <div className="flex flex-col h-full">
      <div className="px-5 py-4 border-b border-[#1e3a5f]">
        <div className="font-display font-700 text-xl tracking-[0.1em] text-[#e2eaf5]">SYSTEM SETTINGS</div>
        <div className="font-mono-data text-[10px] text-[#3d6490] tracking-widest">NETRIXA CONFIGURATION · DEMO MODE ACTIVE</div>
      </div>
      <div className="p-5 max-w-2xl space-y-4">
        {[
          { label: 'RISK THRESHOLDS', items: [
            { k: 'Low threshold', v: '0 – 25', editable: true },
            { k: 'Medium threshold', v: '26 – 50', editable: true },
            { k: 'High threshold', v: '51 – 75', editable: true },
            { k: 'Critical threshold', v: '76 – 100', editable: true },
          ]},
          { label: 'DATA PIPELINE', items: [
            { k: 'FIRMS API Key', v: '••••••••••••••••', editable: true },
            { k: 'Demo Mode', v: 'ENABLED', editable: false },
            { k: 'Data refresh interval', v: '6 hours', editable: true },
          ]},
          { label: 'SYSTEM STATUS', items: [
            { k: 'Application version', v: 'NETRIXA v0.1.0 · SIH 2026 PROTOTYPE' },
            { k: 'Build date', v: '2026-09-04' },
            { k: 'Problem Statement', v: 'SIH 2026 · #26162' },
          ]},
        ].map(({ label, items }) => (
          <div key={label} className="bg-[#0a1628] border border-[#1e3a5f]">
            <div className="px-4 py-2.5 border-b border-[#1e3a5f] font-mono-data text-[9px] text-[#3d6490] tracking-widest">{label}</div>
            <div className="p-4 space-y-3">
              {items.map(({ k, v, ...rest }) => { const editable = 'editable' in rest ? rest.editable : false; return (
                <div key={k} className="flex items-center justify-between gap-4">
                  <span className="font-mono-data text-xs text-[#7a9cc4]">{k}</span>
                  {editable ? (
                    <input defaultValue={v} className="bg-[#050a14] border border-[#1e3a5f] text-[#e2eaf5] font-mono-data text-xs px-2 py-1 w-48 focus:outline-none focus:border-cyan-500/50" />
                  ) : (
                    <span className="font-mono-data text-xs text-[#3d6490]">{v}</span>
                  )}
                </div>
              );})}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

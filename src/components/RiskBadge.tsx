import type { RiskLevel } from '../types';

interface Props {
  level: RiskLevel;
  pulse?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const configs: Record<RiskLevel, { label: string; bg: string; text: string; border: string }> = {
  LOW: { label: 'LOW', bg: 'bg-green-950/60', text: 'text-green-400', border: 'border-green-800/50' },
  MEDIUM: { label: 'MEDIUM', bg: 'bg-amber-950/60', text: 'text-amber-400', border: 'border-amber-800/50' },
  HIGH: { label: 'HIGH', bg: 'bg-orange-950/60', text: 'text-orange-400', border: 'border-orange-800/50' },
  CRITICAL: { label: 'CRITICAL', bg: 'bg-red-950/60', text: 'text-red-400', border: 'border-red-800/50' },
};

const sizes = {
  sm: 'text-[10px] px-1.5 py-0.5',
  md: 'text-xs px-2 py-1',
  lg: 'text-sm px-3 py-1',
};

export default function RiskBadge({ level, pulse, size = 'md' }: Props) {
  const c = configs[level];
  return (
    <span
      className={`inline-flex items-center font-mono-data font-medium tracking-widest border rounded-sm ${c.bg} ${c.text} ${c.border} ${sizes[size]} ${pulse && level === 'CRITICAL' ? 'risk-critical-pulse' : ''}`}
    >
      {c.label}
    </span>
  );
}

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type ClassificationType =
  | 'Potential Industrial Fire'
  | 'Industrial Fire'
  | 'Persistent Industrial Thermal Source'
  | 'Gas Flare'
  | 'Agricultural Burning'
  | 'Wildfire'
  | 'Mining Activity'
  | 'Unknown / Insufficient Evidence';

export type PersistenceType = 'NORMAL_PERSISTENT' | 'ABNORMAL_PERSISTENT' | 'SUDDEN_EVENT' | 'INTERMITTENT' | 'UNKNOWN';

export interface ThermalEvent {
  id: string;
  eventId: string;
  latitude: number;
  longitude: number;
  acquisitionDate: string;
  acquisitionTime: string;
  brightnessTemperature: number;
  frp: number;
  confidence: number;
  satellite: string;
  instrument: string;
  classification: ClassificationType;
  riskScore: number;
  riskLevel: RiskLevel;
  state: string;
  district: string;
  facilityName?: string;
  facilityDistance?: number;
  facilityType?: string;
  landCover: string;
  historicalMean: number;
  historicalStd: number;
  currentDeviation: number;
  zScore: number;
  persistence: PersistenceType;
  observations: number;
  firstObserved: string;
  lastObserved: string;
  anomalyScore: number;
  industrialProximity: 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';
  explanation: ExplanationFactor[];
  classificationProbabilities: Record<string, number>;
  recommendedAction: string;
  spatialChange: 'HIGH' | 'MEDIUM' | 'LOW' | 'STABLE';
  historicalData: HistoricalPoint[];
}

export interface ExplanationFactor {
  factor: string;
  value: 'HIGH' | 'MEDIUM' | 'LOW';
  confirmed: boolean;
  description: string;
}

export interface HistoricalPoint {
  date: string;
  intensity: number;
  frp: number;
  isAnomaly?: boolean;
}

export interface Facility {
  id: string;
  facilityId: string;
  name: string;
  facilityType: string;
  latitude: number;
  longitude: number;
  state: string;
  district: string;
  status: 'NORMAL' | 'WATCH' | 'ABNORMAL' | 'CRITICAL';
  thermalActivity30d: number;
  thermalActivity90d: number;
  nearbyEvents: number;
  lastActivity: string;
}

export interface Alert {
  id: string;
  eventId: string;
  severity: RiskLevel;
  title: string;
  message: string;
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
  createdAt: string;
  resolvedAt?: string;
  recommendedAction: string;
}

export interface DashboardSummary {
  totalEvents: number;
  industrialEvents: number;
  potentialIndustrialFires: number;
  criticalEvents: number;
  persistentSources: number;
}

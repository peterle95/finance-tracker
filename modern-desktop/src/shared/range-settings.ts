export type JourneyHorizonPreset = "90-days" | "12-months" | "5-years" | "10-years" | "20-years";

export interface DefaultRangeSettings {
  projectionMonths: number;
  projectionHistoryMonths: number;
  carryoverMonths: number;
  reportHistoryMonths: number;
  reportLineMonths: number;
  journeyHorizon: JourneyHorizonPreset;
}

export const DEFAULT_RANGE_SETTINGS: DefaultRangeSettings = {
  projectionMonths: 12,
  projectionHistoryMonths: 6,
  carryoverMonths: 3,
  reportHistoryMonths: 6,
  reportLineMonths: 6,
  journeyHorizon: "12-months"
};

export const RANGE_SETTING_LIMITS = {
  projectionMonths: { min: 3, max: 36 },
  projectionHistoryMonths: { min: 1, max: 120 },
  carryoverMonths: { min: 1, max: 24 },
  reportHistoryMonths: { min: 2, max: 24 },
  reportLineMonths: { min: 1, max: 24 }
} as const;

function boundedNumber(value: unknown, fallback: number, min: number, max: number): number {
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  return Math.min(max, Math.max(min, Math.floor(parsed)));
}

export function normalizeDefaultRangeSettings(value: unknown): DefaultRangeSettings {
  const source = value && typeof value === "object" && !Array.isArray(value)
    ? value as Partial<DefaultRangeSettings>
    : {};
  const journeyHorizon = source.journeyHorizon;

  return {
    projectionMonths: boundedNumber(source.projectionMonths, DEFAULT_RANGE_SETTINGS.projectionMonths, RANGE_SETTING_LIMITS.projectionMonths.min, RANGE_SETTING_LIMITS.projectionMonths.max),
    projectionHistoryMonths: boundedNumber(source.projectionHistoryMonths, DEFAULT_RANGE_SETTINGS.projectionHistoryMonths, RANGE_SETTING_LIMITS.projectionHistoryMonths.min, RANGE_SETTING_LIMITS.projectionHistoryMonths.max),
    carryoverMonths: boundedNumber(source.carryoverMonths, DEFAULT_RANGE_SETTINGS.carryoverMonths, RANGE_SETTING_LIMITS.carryoverMonths.min, RANGE_SETTING_LIMITS.carryoverMonths.max),
    reportHistoryMonths: boundedNumber(source.reportHistoryMonths, DEFAULT_RANGE_SETTINGS.reportHistoryMonths, RANGE_SETTING_LIMITS.reportHistoryMonths.min, RANGE_SETTING_LIMITS.reportHistoryMonths.max),
    reportLineMonths: boundedNumber(source.reportLineMonths, DEFAULT_RANGE_SETTINGS.reportLineMonths, RANGE_SETTING_LIMITS.reportLineMonths.min, RANGE_SETTING_LIMITS.reportLineMonths.max),
    journeyHorizon: journeyHorizon === "90-days" || journeyHorizon === "12-months" || journeyHorizon === "5-years" || journeyHorizon === "10-years" || journeyHorizon === "20-years"
      ? journeyHorizon
      : DEFAULT_RANGE_SETTINGS.journeyHorizon
  };
}

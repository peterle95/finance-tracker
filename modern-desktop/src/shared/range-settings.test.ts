import { describe, expect, it } from "vitest";
import { DEFAULT_RANGE_SETTINGS, normalizeDefaultRangeSettings } from "./range-settings";

describe("default range settings", () => {
  it("fills missing values with the application defaults", () => {
    expect(normalizeDefaultRangeSettings({ projectionMonths: 18 })).toEqual({
      ...DEFAULT_RANGE_SETTINGS,
      projectionMonths: 18
    });
  });

  it("clamps numeric values and rejects unknown journey presets", () => {
    expect(normalizeDefaultRangeSettings({
      projectionMonths: 100,
      projectionHistoryMonths: 0,
      carryoverMonths: -5,
      reportHistoryMonths: 1,
      reportLineMonths: 99,
      journeyHorizon: "not-a-preset"
    })).toEqual({
      projectionMonths: 36,
      projectionHistoryMonths: 1,
      carryoverMonths: 1,
      reportHistoryMonths: 2,
      reportLineMonths: 24,
      journeyHorizon: "12-months"
    });
  });
});

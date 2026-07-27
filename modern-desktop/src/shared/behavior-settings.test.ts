import { describe, expect, it } from "vitest";
import { DEFAULT_BEHAVIOR_SETTINGS, normalizeDefaultBehaviorSettings } from "./behavior-settings";

describe("default behavior settings", () => {
  it("fills missing behavior values with current defaults", () => {
    expect(normalizeDefaultBehaviorSettings({ reportDateBasis: "behavior" })).toEqual({
      ...DEFAULT_BEHAVIOR_SETTINGS,
      reportDateBasis: "behavior"
    });
  });

  it("rejects unsupported values while preserving valid booleans", () => {
    expect(normalizeDefaultBehaviorSettings({
      includeNegativeCarryover: false,
      projectionMode: "unsupported",
      reportView: "unsupported",
      reportHistoryDisplay: "unsupported"
    })).toEqual({
      ...DEFAULT_BEHAVIOR_SETTINGS,
      includeNegativeCarryover: false
    });
  });
});

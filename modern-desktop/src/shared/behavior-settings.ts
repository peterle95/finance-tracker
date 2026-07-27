export type DefaultProjectionMode = "target" | "net-worth";
export type DefaultNetWorthChangeMode = "month-by-month" | "from-beginning";
export type DefaultReportView = "pie" | "history" | "line" | "heatmap" | "pace";
export type DefaultReportType = "Expense" | "Income";
export type DefaultReportDateBasis = "transaction" | "behavior";
export type DefaultReportHistoryMode = "total" | "categories" | "flexible" | "over-under";
export type DefaultReportHistoryDisplay = "value" | "percentage";

export interface DefaultBehaviorSettings {
  includeNegativeCarryover: boolean;
  projectionMode: DefaultProjectionMode;
  netWorthChangeMode: DefaultNetWorthChangeMode;
  reportView: DefaultReportView;
  reportType: DefaultReportType;
  reportDateBasis: DefaultReportDateBasis;
  reportHistoryMode: DefaultReportHistoryMode;
  reportHistoryDisplay: DefaultReportHistoryDisplay;
  reportIncludeRecurring: boolean;
  reportShowHistoryLabels: boolean;
}

export const DEFAULT_BEHAVIOR_SETTINGS: DefaultBehaviorSettings = {
  includeNegativeCarryover: true,
  projectionMode: "target",
  netWorthChangeMode: "month-by-month",
  reportView: "pie",
  reportType: "Expense",
  reportDateBasis: "transaction",
  reportHistoryMode: "total",
  reportHistoryDisplay: "value",
  reportIncludeRecurring: false,
  reportShowHistoryLabels: false
};

export function normalizeDefaultBehaviorSettings(value: unknown): DefaultBehaviorSettings {
  const source = value && typeof value === "object" && !Array.isArray(value)
    ? value as Partial<DefaultBehaviorSettings>
    : {};

  return {
    includeNegativeCarryover: typeof source.includeNegativeCarryover === "boolean"
      ? source.includeNegativeCarryover
      : DEFAULT_BEHAVIOR_SETTINGS.includeNegativeCarryover,
    projectionMode: source.projectionMode === "target" || source.projectionMode === "net-worth"
      ? source.projectionMode
      : DEFAULT_BEHAVIOR_SETTINGS.projectionMode,
    netWorthChangeMode: source.netWorthChangeMode === "month-by-month" || source.netWorthChangeMode === "from-beginning"
      ? source.netWorthChangeMode
      : DEFAULT_BEHAVIOR_SETTINGS.netWorthChangeMode,
    reportView: source.reportView === "pie" || source.reportView === "history" || source.reportView === "line" || source.reportView === "heatmap" || source.reportView === "pace"
      ? source.reportView
      : DEFAULT_BEHAVIOR_SETTINGS.reportView,
    reportType: source.reportType === "Expense" || source.reportType === "Income"
      ? source.reportType
      : DEFAULT_BEHAVIOR_SETTINGS.reportType,
    reportDateBasis: source.reportDateBasis === "transaction" || source.reportDateBasis === "behavior"
      ? source.reportDateBasis
      : DEFAULT_BEHAVIOR_SETTINGS.reportDateBasis,
    reportHistoryMode: source.reportHistoryMode === "total" || source.reportHistoryMode === "categories" || source.reportHistoryMode === "flexible" || source.reportHistoryMode === "over-under"
      ? source.reportHistoryMode
      : DEFAULT_BEHAVIOR_SETTINGS.reportHistoryMode,
    reportHistoryDisplay: source.reportHistoryDisplay === "value" || source.reportHistoryDisplay === "percentage"
      ? source.reportHistoryDisplay
      : DEFAULT_BEHAVIOR_SETTINGS.reportHistoryDisplay,
    reportIncludeRecurring: typeof source.reportIncludeRecurring === "boolean"
      ? source.reportIncludeRecurring
      : DEFAULT_BEHAVIOR_SETTINGS.reportIncludeRecurring,
    reportShowHistoryLabels: typeof source.reportShowHistoryLabels === "boolean"
      ? source.reportShowHistoryLabels
      : DEFAULT_BEHAVIOR_SETTINGS.reportShowHistoryLabels
  };
}

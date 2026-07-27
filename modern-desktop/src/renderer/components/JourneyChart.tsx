import { useEffect, useState, type KeyboardEvent } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  buildJourneyDataset,
  DEFAULT_JOURNEY_HORIZON,
  type JourneyDataset,
  type JourneyHorizon,
  type JourneySeries
} from "../../shared/journey";
import type { JourneyHorizonPreset } from "../../shared/range-settings";
import { formatCurrency, monthOffset } from "../../shared/finance";
import type { FinanceDocument } from "../../shared/types";
import { tooltipStyle, tooltipTextStyle } from "./chartStyles";
import { Card } from "./ui";

const horizonOptions: Array<{ value: string; label: string; horizon: JourneyHorizon }> = [
  { value: "90-days", label: "90 days · Daily", horizon: { amount: 90, unit: "days" } },
  { value: "12-months", label: "12 months · Monthly", horizon: { amount: 12, unit: "months" } },
  { value: "5-years", label: "5 years · Yearly", horizon: { amount: 5, unit: "years" } },
  { value: "10-years", label: "10 years · Yearly", horizon: { amount: 10, unit: "years" } },
  { value: "20-years", label: "20 years · Yearly", horizon: { amount: 20, unit: "years" } }
];

function horizonFromPreset(preset: JourneyHorizonPreset): JourneyHorizon {
  return horizonOptions.find((option) => option.value === preset)?.horizon ?? DEFAULT_JOURNEY_HORIZON;
}

const seriesColors: Record<JourneySeries["state"], string> = {
  actual: "#f5c451",
  projected: "#2dd4bf",
  scenario: "#a78bfa"
};

function nextJourneyDate(date: string, resolution: JourneyDataset["resolution"]): string {
  if (resolution === "monthly") {
    return monthOffset(date, 1);
  }
  if (resolution === "yearly") {
    return String(Number(date) + 1);
  }
  const next = new Date(date + "T12:00:00Z");
  next.setUTCDate(next.getUTCDate() + 1);
  return next.toISOString().slice(0, 10);
}

function chartRows(dataset: JourneyDataset): Array<Record<string, string | number | null>> {
  const dates = new Set(dataset.timeline);
  const actual = dataset.series.find((series) => series.state === "actual")?.points ?? [];
  actual.forEach((point, index) => {
    const next = actual[index + 1]?.date;
    let cursor = point.date;
    while (next && cursor < next) {
      cursor = nextJourneyDate(cursor, dataset.resolution);
      if (cursor < next) {
        dates.add(cursor);
      }
    }
  });

  return [...dates].sort().map((date) => {
    const row: Record<string, string | number | null> = { date };
    dataset.series.forEach((series) => {
      row[series.id] = series.points.find((point) => point.date === date)?.value ?? null;
    });
    return row;
  });
}

function seriesPoint(dataset: JourneyDataset, series: JourneySeries, date: string) {
  return series.points.find((point) => point.date === date);
}

export function JourneyChart({ document, defaultHorizon = "12-months", reducedMotion = false }: { document: FinanceDocument; defaultHorizon?: JourneyHorizonPreset; reducedMotion?: boolean }) {
  const [horizon, setHorizon] = useState<JourneyHorizon>(() => horizonFromPreset(defaultHorizon));
  const [selectedIndex, setSelectedIndex] = useState(0);
  const dataset = buildJourneyDataset(document, horizon);
  const rows = chartRows(dataset);
  const selectedDate = dataset.timeline[selectedIndex] ?? dataset.timeline[0] ?? "No data";
  const selectedSeries = dataset.series.map((series) => ({ series, point: seriesPoint(dataset, series, selectedDate) }));
  const selectedPoint = selectedSeries.find((entry) => entry.point)?.point;

  useEffect(() => {
    setSelectedIndex((index) => Math.min(index, Math.max(0, dataset.timeline.length - 1)));
  }, [dataset.timeline.length]);

  function changeHorizon(value: string) {
    const option = horizonOptions.find((entry) => entry.value === value);
    if (!option) {
      return;
    }
    setHorizon(option.horizon);
    setSelectedIndex(0);
  }

  function selectMarker(date: string) {
    const index = dataset.timeline.indexOf(date);
    if (index >= 0) {
      setSelectedIndex(index);
    }
  }

  function moveScrubber(event: KeyboardEvent<HTMLInputElement>) {
    const lastIndex = Math.max(0, dataset.timeline.length - 1);
    if (event.key === "Home") {
      event.preventDefault();
      setSelectedIndex(0);
    } else if (event.key === "End") {
      event.preventDefault();
      setSelectedIndex(lastIndex);
    } else if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
      event.preventDefault();
      setSelectedIndex((index) => Math.max(0, index - 1));
    } else if (event.key === "ArrowRight" || event.key === "ArrowUp") {
      event.preventDefault();
      setSelectedIndex((index) => Math.min(lastIndex, index + 1));
    }
  }

  return (
    <div className="journey-workspace">
      <Card className="journey-chart-card">
        <div className="card-heading">
          <div><p className="eyebrow">Net-worth journey</p><h2>History, baseline, and what-if space</h2></div>
        </div>
        <div className="journey-toolbar">
          <label className="control-label">Horizon<select aria-label="Journey horizon" value={horizonOptions.find((option) => option.horizon.amount === horizon.amount && option.horizon.unit === horizon.unit)?.value} onChange={(event) => changeHorizon(event.target.value)}>{horizonOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
          <div className="journey-confidence" aria-label="Journey confidence"><span>Confidence</span><strong>{dataset.confidence.level}</strong><small>{dataset.resolution} · {dataset.confidence.actualPoints} actual point(s)</small></div>
        </div>
        <div className="journey-legend" aria-label="Journey series legend">
          {dataset.series.map((series) => <div className="journey-legend-item" key={series.id} data-series-style={series.style}><span className="journey-series-swatch" style={{ borderTopColor: seriesColors[series.state] }} /><span>{series.label}</span><small>{series.style === "solid" ? "Recorded" : series.style === "dashed" ? "Baseline" : "Scenario-ready"}</small></div>)}
        </div>
        <div className="journey-chart-shell" aria-label="Net-worth journey chart">
          <ResponsiveContainer width="100%" height={340}>
            <LineChart data={rows} margin={{ top: 12, right: 18, left: 6, bottom: 8 }} onClick={(state) => { if (typeof state?.activeLabel === "string") { selectMarker(state.activeLabel); } }}>
              <CartesianGrid stroke="rgba(162, 196, 187, 0.12)" strokeDasharray="3 3" />
              <XAxis dataKey="date" tickLine={false} axisLine={false} minTickGap={24} />
              <YAxis tickFormatter={(value) => "€" + Math.round(value)} tickLine={false} axisLine={false} width={76} />
              <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipTextStyle} itemStyle={tooltipTextStyle} formatter={(value) => formatCurrency(Number(value))} />
              {dataset.series.map((series) => <Line key={series.id} type="monotone" dataKey={series.id} name={series.label} stroke={seriesColors[series.state]} strokeWidth={series.state === "actual" ? 3 : 2} strokeDasharray={series.style === "dashed" ? "8 5" : series.style === "accent" ? "2 4" : undefined} dot={series.state === "scenario" ? false : { r: 3 }} connectNulls={false} isAnimationActive={!reducedMotion} animationDuration={reducedMotion ? 0 : 300} />)}
            </LineChart>
          </ResponsiveContainer>
        </div>
        <label className="journey-scrubber"><span>Timeline<strong>{selectedDate}</strong></span><input aria-label="Journey timeline scrubber" type="range" min="0" max={Math.max(0, dataset.timeline.length - 1)} value={selectedIndex} onChange={(event) => setSelectedIndex(Number(event.target.value))} onKeyDown={moveScrubber} /></label>
        <p className="journey-status" role="status" aria-live="polite">Selected {selectedDate}. {selectedPoint ? formatCurrency(selectedPoint.value) + " from " + selectedPoint.source + "." : "No recorded value at selected period."}</p>
      </Card>

      <div className="journey-detail-grid">
        <Card>
          <div className="card-heading"><div><p className="eyebrow">Driver details</p><h2>{selectedDate}</h2></div></div>
          {selectedPoint ? <div className="journey-selected-summary"><span>Selected value</span><strong>{formatCurrency(selectedPoint.value)}</strong><small>Date: {selectedPoint.date} · Source: {selectedPoint.source}</small></div> : <p className="muted-copy">No actual or projected value is available at this period.</p>}
          <div className="journey-driver-list">
            {selectedSeries.flatMap(({ series, point }) => point
              ? Object.entries(point.drivers).map(([driverId, value]) => {
                const driver = dataset.drivers.find((entry) => entry.id === driverId);
                return <div key={series.id + driverId}><span>{driver?.label ?? driverId}<small>{driver?.source ?? point.source} · {point.date}</small></span><strong>{formatCurrency(value)}</strong></div>;
              })
              : [])}
          </div>
        </Card>
        <Card>
          <div className="card-heading"><div><p className="eyebrow">Turning points</p><h2>Inspect changes</h2></div></div>
          {dataset.turningPoints.length ? <div className="journey-marker-list">{dataset.turningPoints.map((marker, index) => <button type="button" className="journey-marker" key={marker.date + marker.reason + index} aria-label={"Turning point " + marker.date + ": " + marker.explanation} onClick={() => selectMarker(marker.date)}><span><strong>{marker.date}</strong><small>{marker.reason}</small></span><span>{marker.explanation}</span></button>)}</div> : <p className="muted-copy">No turning points in selected history.</p>}
          <p className="journey-assumption">{dataset.assumptions[0]}</p>
        </Card>
      </div>
    </div>
  );
}

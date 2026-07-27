import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import {
  DEFAULT_RANGE_SETTINGS,
  normalizeDefaultRangeSettings,
  RANGE_SETTING_LIMITS,
  type DefaultRangeSettings,
  type JourneyHorizonPreset
} from "../../shared/range-settings";
import { Button } from "./ui";

interface DefaultRangesDialogProps {
  open: boolean;
  settings: DefaultRangeSettings;
  onOpenChange(open: boolean): void;
  onSave(settings: DefaultRangeSettings): void;
}

const journeyOptions: Array<{ value: JourneyHorizonPreset; label: string }> = [
  { value: "90-days", label: "90 days" },
  { value: "12-months", label: "12 months" },
  { value: "5-years", label: "5 years" },
  { value: "10-years", label: "10 years" },
  { value: "20-years", label: "20 years" }
];

export function DefaultRangesDialog({ open, settings, onOpenChange, onSave }: DefaultRangesDialogProps) {
  const [draft, setDraft] = useState(settings);

  useEffect(() => {
    if (open) {
      setDraft(settings);
    }
  }, [open, settings]);

  function updateNumber(key: keyof Pick<DefaultRangeSettings, "projectionMonths" | "projectionHistoryMonths" | "carryoverMonths" | "reportHistoryMonths" | "reportLineMonths">, value: string) {
    setDraft((current) => ({ ...current, [key]: value === "" ? 0 : Number(value) }));
  }

  function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSave(normalizeDefaultRangeSettings(draft));
    onOpenChange(false);
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content default-ranges-dialog" aria-describedby="default-ranges-description">
          <div className="dialog-heading">
            <div>
              <p className="eyebrow">Application defaults</p>
              <Dialog.Title>Default ranges</Dialog.Title>
              <Dialog.Description id="default-ranges-description">
                Choose the period each feature opens with. Allowed ranges keep calculations practical.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button className="icon-button" aria-label="Close default ranges">
                <X size={18} />
              </button>
            </Dialog.Close>
          </div>

          <form className="form-grid default-ranges-form" onSubmit={save}>
            <label>
              <span>Projection months</span>
              <input aria-label="Projection months" type="number" min={RANGE_SETTING_LIMITS.projectionMonths.min} max={RANGE_SETTING_LIMITS.projectionMonths.max} value={draft.projectionMonths || ""} onChange={(event) => updateNumber("projectionMonths", event.target.value)} required />
              <small>{RANGE_SETTING_LIMITS.projectionMonths.min}–{RANGE_SETTING_LIMITS.projectionMonths.max} months</small>
            </label>
            <label>
              <span>Projection history months</span>
              <input aria-label="Projection history months" type="number" min={RANGE_SETTING_LIMITS.projectionHistoryMonths.min} max={RANGE_SETTING_LIMITS.projectionHistoryMonths.max} value={draft.projectionHistoryMonths || ""} onChange={(event) => updateNumber("projectionHistoryMonths", event.target.value)} required />
              <small>{RANGE_SETTING_LIMITS.projectionHistoryMonths.min}–{RANGE_SETTING_LIMITS.projectionHistoryMonths.max} months</small>
            </label>
            <label>
              <span>Budget carryover months</span>
              <input aria-label="Budget carryover months" type="number" min={RANGE_SETTING_LIMITS.carryoverMonths.min} max={RANGE_SETTING_LIMITS.carryoverMonths.max} value={draft.carryoverMonths || ""} onChange={(event) => updateNumber("carryoverMonths", event.target.value)} required />
              <small>{RANGE_SETTING_LIMITS.carryoverMonths.min}–{RANGE_SETTING_LIMITS.carryoverMonths.max} months</small>
            </label>
            <label>
              <span>Report history months</span>
              <input aria-label="Report history months" type="number" min={RANGE_SETTING_LIMITS.reportHistoryMonths.min} max={RANGE_SETTING_LIMITS.reportHistoryMonths.max} value={draft.reportHistoryMonths || ""} onChange={(event) => updateNumber("reportHistoryMonths", event.target.value)} required />
              <small>{RANGE_SETTING_LIMITS.reportHistoryMonths.min}–{RANGE_SETTING_LIMITS.reportHistoryMonths.max} months</small>
            </label>
            <label>
              <span>Report line range months</span>
              <input aria-label="Report line range months" type="number" min={RANGE_SETTING_LIMITS.reportLineMonths.min} max={RANGE_SETTING_LIMITS.reportLineMonths.max} value={draft.reportLineMonths || ""} onChange={(event) => updateNumber("reportLineMonths", event.target.value)} required />
              <small>{RANGE_SETTING_LIMITS.reportLineMonths.min}–{RANGE_SETTING_LIMITS.reportLineMonths.max} months</small>
            </label>
            <label>
              <span>Net-worth journey horizon</span>
              <select aria-label="Net-worth journey horizon" value={draft.journeyHorizon} onChange={(event) => setDraft((current) => ({ ...current, journeyHorizon: event.target.value as JourneyHorizonPreset }))}>
                {journeyOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
              <small>Used when opening the journey view</small>
            </label>
            <div className="dialog-actions span-two">
              <Button type="button" variant="ghost" onClick={() => setDraft(DEFAULT_RANGE_SETTINGS)}>Reset defaults</Button>
              <Dialog.Close asChild><Button type="button" variant="ghost">Cancel</Button></Dialog.Close>
              <Button type="submit">Save ranges</Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import {
  DEFAULT_BEHAVIOR_SETTINGS,
  normalizeDefaultBehaviorSettings,
  type DefaultBehaviorSettings
} from "../../shared/behavior-settings";
import { Button } from "./ui";

interface DefaultBehaviorsDialogProps {
  open: boolean;
  settings: DefaultBehaviorSettings;
  onOpenChange(open: boolean): void;
  onSave(settings: DefaultBehaviorSettings): void;
}

export function DefaultBehaviorsDialog({ open, settings, onOpenChange, onSave }: DefaultBehaviorsDialogProps) {
  const [draft, setDraft] = useState(settings);

  useEffect(() => {
    if (open) {
      setDraft(settings);
    }
  }, [open, settings]);

  function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSave(normalizeDefaultBehaviorSettings(draft));
    onOpenChange(false);
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content default-behaviors-dialog" aria-describedby="default-behaviors-description">
          <div className="dialog-heading">
            <div>
              <p className="eyebrow">Application defaults</p>
              <Dialog.Title>Default behaviors</Dialog.Title>
              <Dialog.Description id="default-behaviors-description">
                Choose what each workspace shows and includes when it opens.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button className="icon-button" aria-label="Close default behaviors"><X size={18} /></button>
            </Dialog.Close>
          </div>

          <form className="form-grid default-behaviors-form" onSubmit={save}>
            <label className="span-two check-row">
              <input type="checkbox" checked={draft.includeNegativeCarryover} onChange={(event) => setDraft((current) => ({ ...current, includeNegativeCarryover: event.target.checked }))} />
              <span>Include negative carryover by default in Budget</span>
            </label>

            <label>
              <span>Default projection mode</span>
              <select aria-label="Default projection mode" value={draft.projectionMode} onChange={(event) => setDraft((current) => ({ ...current, projectionMode: event.target.value as DefaultBehaviorSettings["projectionMode"] }))}>
                <option value="target">Target savings</option>
                <option value="net-worth">Net worth trend</option>
              </select>
            </label>
            <label>
              <span>Net-worth change mode</span>
              <select aria-label="Net-worth change mode" value={draft.netWorthChangeMode} onChange={(event) => setDraft((current) => ({ ...current, netWorthChangeMode: event.target.value as DefaultBehaviorSettings["netWorthChangeMode"] }))}>
                <option value="month-by-month">Month-by-month</option>
                <option value="from-beginning">Since beginning</option>
              </select>
            </label>

            <label>
              <span>Default report view</span>
              <select aria-label="Default report view" value={draft.reportView} onChange={(event) => setDraft((current) => ({ ...current, reportView: event.target.value as DefaultBehaviorSettings["reportView"] }))}>
                <option value="pie">Category overview</option>
                <option value="history">History</option>
                <option value="line">Category trends</option>
                <option value="heatmap">Weekday heatmap</option>
                <option value="pace">Spending pace</option>
              </select>
            </label>
            <label>
              <span>Default report type</span>
              <select aria-label="Default report type" value={draft.reportType} onChange={(event) => setDraft((current) => ({ ...current, reportType: event.target.value as DefaultBehaviorSettings["reportType"] }))}>
                <option value="Expense">Expenses</option>
                <option value="Income">Income</option>
              </select>
            </label>
            <label className="span-two">
              <span>Report date basis</span>
              <select aria-label="Report date basis" value={draft.reportDateBasis} onChange={(event) => setDraft((current) => ({ ...current, reportDateBasis: event.target.value as DefaultBehaviorSettings["reportDateBasis"] }))}>
                <option value="transaction">Transaction date</option>
                <option value="behavior">Behavior date / metadata</option>
              </select>
            </label>

            <label>
              <span>History breakdown</span>
              <select aria-label="Default history breakdown" value={draft.reportHistoryMode} onChange={(event) => setDraft((current) => ({ ...current, reportHistoryMode: event.target.value as DefaultBehaviorSettings["reportHistoryMode"] }))}>
                <option value="total">Total</option>
                <option value="categories">Categories</option>
                <option value="flexible">Flexible income vs costs</option>
                <option value="over-under">Income vs expenses</option>
              </select>
            </label>
            <label>
              <span>History display</span>
              <select aria-label="Default history display" value={draft.reportHistoryDisplay} onChange={(event) => setDraft((current) => ({ ...current, reportHistoryDisplay: event.target.value as DefaultBehaviorSettings["reportHistoryDisplay"] }))}>
                <option value="value">Amounts</option>
                <option value="percentage">Percentage</option>
              </select>
            </label>
            <label className="span-two check-row">
              <input type="checkbox" checked={draft.reportIncludeRecurring} onChange={(event) => setDraft((current) => ({ ...current, reportIncludeRecurring: event.target.checked }))} />
              <span>Include recurring income and costs in reports by default</span>
            </label>
            <label className="span-two check-row">
              <input type="checkbox" checked={draft.reportShowHistoryLabels} onChange={(event) => setDraft((current) => ({ ...current, reportShowHistoryLabels: event.target.checked }))} />
              <span>Show value labels on history charts by default</span>
            </label>

            <div className="dialog-actions span-two">
              <Button type="button" variant="ghost" onClick={() => setDraft(DEFAULT_BEHAVIOR_SETTINGS)}>Reset defaults</Button>
              <Dialog.Close asChild><Button type="button" variant="ghost">Cancel</Button></Dialog.Close>
              <Button type="submit">Save behaviors</Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

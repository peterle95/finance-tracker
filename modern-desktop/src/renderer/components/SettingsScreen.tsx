import { FileCog, Keyboard, Moon, RefreshCw, ShieldAlert, SlidersHorizontal, Sun, Upload } from "lucide-react";
import { useState } from "react";
import type { DefaultBehaviorSettings } from "../../shared/behavior-settings";
import type { DefaultRangeSettings } from "../../shared/range-settings";
import type { DataConnection, FinanceDocument } from "../../shared/types";
import { DefaultBehaviorsDialog } from "./DefaultBehaviorsDialog";
import { DefaultRangesDialog } from "./DefaultRangesDialog";
import { Button, Card, PageHeader } from "./ui";
import { KeyboardNavigationPrototype } from "./KeyboardNavigationPrototype";

type KeyboardNavigationSettings = { activationKey: string; hintAlphabet: string; activationMode: "select" | "immediate" };
const DEFAULT_KEYBOARD_NAVIGATION: KeyboardNavigationSettings = { activationKey: "f", hintAlphabet: "asdfjkl;", activationMode: "select" };

interface SettingsScreenProps {
  document: FinanceDocument;
  connection: DataConnection;
  theme: "dark" | "light";
  reducedMotion: boolean;
  defaultRanges: DefaultRangeSettings;
  defaultBehaviors: DefaultBehaviorSettings;
  onThemeChange(theme: "dark" | "light"): void;
  onReducedMotionChange(reduced: boolean): void;
  onDefaultRangesChange(settings: DefaultRangeSettings): void;
  onDefaultBehaviorsChange(settings: DefaultBehaviorSettings): void;
  onDefaultNetWorthPeriodChange(value: number | "All"): void;
  onDefaultNetWorthBreakdownPeriodChange(value: number | "All"): void;
  onChooseFile(): void;
  onCreateFile(): void;
  onReload(): void;
}

export function SettingsScreen({
  document,
  connection,
  theme,
  reducedMotion,
  defaultRanges,
  defaultBehaviors,
  onThemeChange,
  onReducedMotionChange,
  onDefaultRangesChange,
  onDefaultBehaviorsChange,
  onDefaultNetWorthPeriodChange,
  onDefaultNetWorthBreakdownPeriodChange,
  onChooseFile,
  onCreateFile,
  onReload
}: SettingsScreenProps) {
  const [defaultRangesOpen, setDefaultRangesOpen] = useState(false);
  const [defaultBehaviorsOpen, setDefaultBehaviorsOpen] = useState(false);
  const [keyboardNavigation, setKeyboardNavigation] = useState(DEFAULT_KEYBOARD_NAVIGATION);

  const activationKeyError = keyboardNavigation.activationKey.length !== 1 || /\s/.test(keyboardNavigation.activationKey)
    ? "Use one non-space key."
    : null;
  const alphabet = [...keyboardNavigation.hintAlphabet];
  const hintAlphabetError = alphabet.length < 2 || alphabet.some((key) => /\s/.test(key)) || new Set(alphabet).size !== alphabet.length
    ? "Use at least two unique, non-space characters."
    : null;

  return (
    <div className="page">
      <PageHeader eyebrow="Application" title="Settings" description="Control where the app reads your data and how the workspace feels." />

      <div className="two-column">
        <Card>
          <div className="card-heading"><div><p className="eyebrow">Data connection</p><h2>Shared finance_data.json</h2></div><FileCog size={24} /></div>
          <p className="path-copy">{connection.path ?? "No file connected"}</p>
          <p className="muted-copy">Every save reloads the current file first, then writes the full updated JSON atomically. Unknown fields stay in place for Python and Android compatibility.</p>
          <div className="button-group settings-actions">
            <Button onClick={onChooseFile}><Upload size={16} /> Choose file</Button>
            <Button variant="secondary" onClick={onCreateFile}>Create new file</Button>
            <Button variant="ghost" onClick={onReload}><RefreshCw size={16} /> Reload</Button>
          </div>
          {connection.message ? <p className="error-copy">{connection.message}</p> : null}
        </Card>

        <Card>
          <div className="card-heading"><div><p className="eyebrow">Prototype</p><h2>Keyboard navigation</h2></div><Keyboard size={22} /></div>
          <p className="muted-copy">Configure the proposed keyboard hints. Navigation is not active yet, and these settings reset when the app reloads.</p>
          <div className="form-grid compact-form">
            <label><span>Activation key</span><input aria-label="Activation key" value={keyboardNavigation.activationKey} maxLength={1} onChange={(event) => setKeyboardNavigation((current) => ({ ...current, activationKey: event.target.value }))} />{activationKeyError ? <small className="error-copy">{activationKeyError}</small> : null}</label>
            <label><span>Hint alphabet</span><input aria-label="Hint alphabet" value={keyboardNavigation.hintAlphabet} onChange={(event) => setKeyboardNavigation((current) => ({ ...current, hintAlphabet: event.target.value }))} />{hintAlphabetError ? <small className="error-copy">{hintAlphabetError}</small> : null}</label>
            <div className="span-two"><span className="control-label">Activation behavior</span><div className="theme-choice"><button type="button" className={keyboardNavigation.activationMode === "select" ? "selected" : ""} onClick={() => setKeyboardNavigation((current) => ({ ...current, activationMode: "select" }))}>Select, then Enter</button><button type="button" className={keyboardNavigation.activationMode === "immediate" ? "selected" : ""} onClick={() => setKeyboardNavigation((current) => ({ ...current, activationMode: "immediate" }))}>Activate immediately</button></div></div>
            <div className="form-actions span-two"><Button variant="ghost" onClick={() => setKeyboardNavigation(DEFAULT_KEYBOARD_NAVIGATION)}>Reset keyboard defaults</Button></div>
            <div className="span-two"><KeyboardNavigationPrototype reducedMotion={reducedMotion} /></div>
          </div>
        </Card>

        <Card>
          <div className="card-heading"><div><p className="eyebrow">Appearance</p><h2>Theme</h2></div>{theme === "dark" ? <Moon size={22} /> : <Sun size={22} />}</div>
          <p className="muted-copy">The modern emerald-and-gold palette is available in both high-contrast dark and light modes.</p>
          <div className="theme-choice">
            <button className={theme === "dark" ? "selected" : ""} onClick={() => onThemeChange("dark")}><Moon size={17} /> Dark emerald</button>
            <button className={theme === "light" ? "selected" : ""} onClick={() => onThemeChange("light")}><Sun size={17} /> Light canvas</button>
          </div>
          <label className="check-row motion-choice">
            <input type="checkbox" checked={reducedMotion} onChange={(event) => onReducedMotionChange(event.target.checked)} />
            <span>Reduce nonessential motion</span>
          </label>
          <p className="muted-copy">Disables springs, autoplay, and decorative transitions while keeping values and feedback visible.</p>
        </Card>

        <Card>
          <div className="card-heading"><div><p className="eyebrow">Workspace behavior</p><h2>Default ranges</h2></div><SlidersHorizontal size={22} /></div>
          <p className="muted-copy">Choose the default periods used by projections, carryover, and reports.</p>
          <Button variant="secondary" onClick={() => setDefaultRangesOpen(true)}><SlidersHorizontal size={16} /> Change default ranges</Button>
        </Card>

        <Card>
          <div className="card-heading"><div><p className="eyebrow">Net worth</p><h2>Default Net Worth</h2></div></div>
          <label><span>Default Net Worth</span><select value={String(document.budget_settings.defaultNetWorthPeriod ?? 12)} onChange={(event) => onDefaultNetWorthPeriodChange(event.target.value === "All" ? "All" : Number(event.target.value))}><option>3</option><option>6</option><option>12</option><option>24</option><option>All</option></select></label>
          <label><span>Default Net Worth Breakdown</span><select value={String(document.budget_settings.defaultNetWorthBreakdownPeriod ?? 12)} onChange={(event) => onDefaultNetWorthBreakdownPeriodChange(event.target.value === "All" ? "All" : Number(event.target.value))}><option>3</option><option>6</option><option>12</option><option>24</option><option>All</option></select></label>
        </Card>

        <Card>
          <div className="card-heading"><div><p className="eyebrow">Workspace behavior</p><h2>Default behaviors</h2></div><SlidersHorizontal size={22} /></div>
          <p className="muted-copy">Choose carryover, projection, net-worth, and report behavior used when screens open.</p>
          <Button variant="secondary" onClick={() => setDefaultBehaviorsOpen(true)}><SlidersHorizontal size={16} /> Change default behaviors</Button>
        </Card>
      </div>

      <DefaultRangesDialog open={defaultRangesOpen} settings={defaultRanges} onOpenChange={setDefaultRangesOpen} onSave={onDefaultRangesChange} />
      <DefaultBehaviorsDialog open={defaultBehaviorsOpen} settings={defaultBehaviors} onOpenChange={setDefaultBehaviorsOpen} onSave={onDefaultBehaviorsChange} />

      <Card className="notice-card">
        <ShieldAlert size={22} />
        <div>
          <h2>Syncthing safety</h2>
          <p>This file is the single source of truth. Avoid editing it from this app, the Python app, and Android at the exact same second. Enable Syncthing versioning so any conflict can be recovered.</p>
        </div>
      </Card>

      <Card>
        <div className="card-heading"><div><p className="eyebrow">Compatibility</p><h2>What this app preserves</h2></div></div>
        <div className="compatibility-grid">
          <span>Expenses: {document.expenses.length}</span>
          <span>Income records: {document.incomes.length}</span>
          <span>Expense categories: {document.categories.Expense.length}</span>
          <span>Income categories: {document.categories.Income.length}</span>
          <span>AI settings: preserved but unused in v1</span>
          <span>Unknown JSON fields: retained on save</span>
        </div>
      </Card>
    </div>
  );
}

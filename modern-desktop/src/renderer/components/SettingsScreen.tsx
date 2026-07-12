import { FileCog, Moon, RefreshCw, ShieldAlert, Sun, Upload } from "lucide-react";
import type { DataConnection, FinanceDocument } from "../../shared/types";
import { Button, Card, PageHeader } from "./ui";

interface SettingsScreenProps {
  document: FinanceDocument;
  connection: DataConnection;
  theme: "dark" | "light";
  onThemeChange(theme: "dark" | "light"): void;
  onChooseFile(): void;
  onCreateFile(): void;
  onReload(): void;
}

export function SettingsScreen({
  document,
  connection,
  theme,
  onThemeChange,
  onChooseFile,
  onCreateFile,
  onReload
}: SettingsScreenProps) {
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
          <div className="card-heading"><div><p className="eyebrow">Appearance</p><h2>Theme</h2></div>{theme === "dark" ? <Moon size={22} /> : <Sun size={22} />}</div>
          <p className="muted-copy">The modern emerald-and-gold palette is available in both high-contrast dark and light modes.</p>
          <div className="theme-choice">
            <button className={theme === "dark" ? "selected" : ""} onClick={() => onThemeChange("dark")}><Moon size={17} /> Dark emerald</button>
            <button className={theme === "light" ? "selected" : ""} onClick={() => onThemeChange("light")}><Sun size={17} /> Light canvas</button>
          </div>
        </Card>
      </div>

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

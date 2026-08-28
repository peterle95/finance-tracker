import {
  BarChart3,
  ChevronLeft,
  ChevronRight,
  FileCheck2,
  LayoutDashboard,
  LineChart,
  Menu,
  Moon,
  ReceiptText,
  Settings,
  SlidersHorizontal,
  Target,
  TrendingUp,
  WalletCards
} from "lucide-react";
import { useEffect, useState } from "react";
import { cloneDocument } from "../shared/finance";
import { normalizeDefaultBehaviorSettings } from "../shared/behavior-settings";
import { normalizeDefaultRangeSettings } from "../shared/range-settings";
import type {
  DataConnection,
  DataLoadResult,
  FinanceDocument,
  FinanceTransaction,
  TransactionType
} from "../shared/types";
import { BudgetScreen } from "./components/BudgetScreen";
import { CategoryLimitsScreen } from "./components/CategoryLimitsScreen";
import { DashboardScreen } from "./components/DashboardScreen";
import { GoalsScreen } from "./components/GoalsScreen";
import { NetWorthScreen } from "./components/NetWorthScreen";
import { ProjectionScreen } from "./components/ProjectionScreen";
import { ReconciliationScreen } from "./components/ReconciliationScreen";
import { ReportsScreen } from "./components/ReportsScreen";
import { SettingsScreen } from "./components/SettingsScreen";
import { TransactionEditor } from "./components/TransactionEditor";
import { TransactionsScreen } from "./components/TransactionsScreen";
import { Button, LoadingScreen } from "./components/ui";
import { useKeyboardNavigation } from "./keyboard-navigation";

type Page = "dashboard" | "transactions" | "budget" | "category-limits" | "goals" | "reports" | "net-worth" | "projection" | "reconciliation" | "settings";
type Theme = "dark" | "light";

const navigation: Array<{ page: Page; label: string; icon: typeof LayoutDashboard }> = [
  { page: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { page: "transactions", label: "Transactions", icon: ReceiptText },
  { page: "budget", label: "Budget", icon: WalletCards },
  { page: "category-limits", label: "Category limits", icon: SlidersHorizontal },
  { page: "goals", label: "Goals", icon: Target },
  { page: "reports", label: "Reports", icon: BarChart3 },
  { page: "net-worth", label: "Net worth", icon: LineChart },
  { page: "projection", label: "Projection", icon: TrendingUp },
  { page: "reconciliation", label: "Reconciliation", icon: FileCheck2 }
];

interface EditorState {
  type: TransactionType;
  transaction?: FinanceTransaction;
}

function initialTheme(): Theme {
  const stored = localStorage.getItem("finance-tracker-theme");
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function initialReducedMotion(): boolean {
  return localStorage.getItem("finance-tracker-reduced-motion") === "true";
}

export function App() {
  const [financeDocument, setDocument] = useState<FinanceDocument | null>(null);
  const [connection, setConnection] = useState<DataConnection>({ path: null, isConnected: false });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [page, setPage] = useState<Page>("dashboard");
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [reducedMotion, setReducedMotion] = useState(initialReducedMotion);
  const [collapsed, setCollapsed] = useState(false);
  const [toast, setToast] = useState("");
  useKeyboardNavigation();

  useEffect(() => {
    window.document.documentElement.dataset.theme = theme;
    localStorage.setItem("finance-tracker-theme", theme);
  }, [theme]);

  useEffect(() => {
    window.document.documentElement.dataset.reducedMotion = String(reducedMotion);
    localStorage.setItem("finance-tracker-reduced-motion", String(reducedMotion));
  }, [reducedMotion]);

  useEffect(() => {
    void loadData();
  }, []);

  function applyLoadResult(result: DataLoadResult) {
    setDocument(result.document);
    setConnection(result.connection);
    setToast(result.warnings?.join(" ") ?? "");
    setLoading(false);
  }

  async function loadData() {
    setLoading(true);
    try {
      applyLoadResult(await window.finance.load());
    } catch {
      applyLoadResult({
        document: null,
        connection: {
          path: null,
          isConnected: false,
          message: "The desktop bridge could not load the finance data."
        }
      });
    }
  }

  async function chooseDataFile() {
    setLoading(true);
    applyLoadResult(await window.finance.chooseDataFile());
  }

  async function createDataFile() {
    setLoading(true);
    applyLoadResult(await window.finance.createDataFile());
  }

  async function persist(next: FinanceDocument) {
    if (!financeDocument) {
      return;
    }
    const previous = financeDocument;
    setDocument(next);
    setSaving(true);
    try {
      const result = await window.finance.saveDocument(previous, next);
      setDocument(result.document);
      setConnection(result.connection);
      setToast("Saved to the shared finance file.");
    } catch (error) {
      setDocument(previous);
      setToast(error instanceof Error ? error.message : "Save failed. Reload the file before trying again.");
    } finally {
      setSaving(false);
      window.setTimeout(() => setToast(""), 2000);
    }
  }

  function saveTransaction(type: TransactionType, transaction: FinanceTransaction, original?: FinanceTransaction) {
    if (!financeDocument) {
      return;
    }
    const currentSource = type === "Expense" ? financeDocument.expenses : financeDocument.incomes;
    const next = cloneDocument(financeDocument);
    const source = type === "Expense" ? next.expenses : next.incomes;
    const index = transaction.id
      ? source.findIndex((entry) => entry.id === transaction.id)
      : original ? currentSource.indexOf(original) : -1;
    if (index >= 0) {
      source[index] = transaction;
    } else {
      source.push(transaction);
    }
    void persist(next);
  }

  function deleteTransaction(type: TransactionType, transaction: FinanceTransaction) {
    if (!financeDocument || !window.confirm("Delete this transaction from the shared finance file?")) {
      return;
    }
    const next = cloneDocument(financeDocument);
    const source = type === "Expense" ? next.expenses : next.incomes;
    const index = source.findIndex((entry) => entry.id && entry.id === transaction.id);
    if (index >= 0) {
      source.splice(index, 1);
    } else {
      const fallback = source.indexOf(transaction);
      if (fallback >= 0) {
        source.splice(fallback, 1);
      }
    }
    void persist(next);
  }

  async function exportText(defaultName: string, text: string) {
    const filePath = await window.finance.exportText(defaultName, text);
    if (filePath) {
      setToast("Report exported.");
      window.setTimeout(() => setToast(""), 2000);
    }
  }

  function navigate(next: Page) {
    setPage(next);
  }

  if (loading) {
    return <LoadingScreen />;
  }

  if (!financeDocument) {
    return (
      <main className="connect-screen">
        <div className="connect-orb" />
        <section className="connect-card">
          <div className="brand-mark">F</div>
          <p className="eyebrow">Finance Tracker Modern</p>
          <h1>Connect your shared finance directory</h1>
          <p>Choose a directory containing modern finance data files or a legacy <code>finance_data.json</code> to migrate.</p>
          {connection.message ? <p className="error-copy">{connection.message}</p> : null}
          <div className="connect-actions">
            <Button onClick={() => void chooseDataFile()}>Choose data directory</Button>
            <Button variant="secondary" onClick={() => void createDataFile()}>Create in directory</Button>
          </div>
          <small>Legacy finance_data.json files are left untouched after migration.</small>
        </section>
      </main>
    );
  }

  const activeDocument = financeDocument;
  const defaultRanges = normalizeDefaultRangeSettings(activeDocument.budget_settings.default_ranges);
  const defaultBehaviors = normalizeDefaultBehaviorSettings(activeDocument.budget_settings.default_behaviors);

  function content() {
    switch (page) {
      case "transactions":
        return <TransactionsScreen document={activeDocument} onAdd={(type) => setEditor({ type })} onEdit={(type, transaction) => setEditor({ type, transaction })} onDelete={deleteTransaction} />;
      case "budget":
        return <BudgetScreen document={activeDocument} defaultRanges={defaultRanges} defaultBehaviors={defaultBehaviors} onSave={(next) => void persist(next)} />;
      case "category-limits":
        return <CategoryLimitsScreen document={activeDocument} onSave={(next) => void persist(next)} />;
      case "goals":
        return <GoalsScreen document={activeDocument} onSave={(next) => void persist(next)} onExport={(name, text) => void exportText(name, text)} />;
      case "reports":
        return <ReportsScreen document={activeDocument} defaultRanges={defaultRanges} defaultBehaviors={defaultBehaviors} onExport={(name, text) => void exportText(name, text)} />;
      case "net-worth":
        return <NetWorthScreen document={activeDocument} defaultBehaviors={defaultBehaviors} defaultNetWorthPeriod={activeDocument.budget_settings.defaultNetWorthPeriod} defaultNetWorthBreakdownPeriod={activeDocument.budget_settings.defaultNetWorthBreakdownPeriod} onSave={(next) => void persist(next)} onExport={(name, text) => void exportText(name, text)} />;
      case "projection":
        return <ProjectionScreen document={activeDocument} defaultRanges={defaultRanges} defaultBehaviors={defaultBehaviors} onExport={(name, text) => void exportText(name, text)} />;
      case "reconciliation":
        return <ReconciliationScreen document={activeDocument} onSave={(next) => void persist(next)} />;
      case "settings":
        return <SettingsScreen document={activeDocument} connection={connection} theme={theme} reducedMotion={reducedMotion} defaultRanges={defaultRanges} defaultBehaviors={defaultBehaviors} onThemeChange={setTheme} onReducedMotionChange={setReducedMotion} onDefaultRangesChange={(next) => {
          const updated = cloneDocument(activeDocument);
          updated.budget_settings.default_ranges = next;
          void persist(updated);
        }} onDefaultBehaviorsChange={(next) => {
          const updated = cloneDocument(activeDocument);
          updated.budget_settings.default_behaviors = next;
          void persist(updated);
        }} onDefaultNetWorthPeriodChange={(value) => { const updated = cloneDocument(activeDocument); updated.budget_settings.defaultNetWorthPeriod = value; void persist(updated); }} onDefaultNetWorthBreakdownPeriodChange={(value) => { const updated = cloneDocument(activeDocument); updated.budget_settings.defaultNetWorthBreakdownPeriod = value; void persist(updated); }} onChooseFile={() => void chooseDataFile()} onCreateFile={() => void createDataFile()} onReload={() => void loadData()} />;
      case "dashboard":
      default:
        return <DashboardScreen document={activeDocument} defaultRanges={defaultRanges} defaultBehaviors={defaultBehaviors} onAddTransaction={(type) => setEditor({ type })} onNavigate={(next) => navigate(next as Page)} />;
    }
  }

  return (
    <div className={"app-shell " + (collapsed ? "sidebar-collapsed" : "")}>
      <aside className="sidebar" data-keyboard-region="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">F</div>
          <div className="brand-copy"><strong>Finance</strong><span>Tracker Modern</span></div>
          <button className="icon-button sidebar-toggle" onClick={() => setCollapsed((value) => !value)} aria-label="Toggle navigation">
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>
        <nav>
          <p className="nav-label">Workspace</p>
          {navigation.map((entry) => {
            const Icon = entry.icon;
            return <button key={entry.page} className={page === entry.page ? "active" : ""} onClick={() => navigate(entry.page)}><Icon size={18} /><span>{entry.label}</span></button>;
          })}
          <p className="nav-label nav-lower">Application</p>
          <button className={page === "settings" ? "active" : ""} onClick={() => navigate("settings")}><Settings size={18} /><span>Settings</span></button>
        </nav>
        <div className="sidebar-footer">
          <span className="connection-dot" />
          <div><strong>Connected</strong><span>{connection.path?.split(/[\\/]/).at(-1) ?? "finance_data.json"}</span></div>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar" data-keyboard-region="header">
          <button className="icon-button mobile-menu" onClick={() => setCollapsed((value) => !value)} aria-label="Toggle menu"><Menu size={20} /></button>
          <div className="topbar-path"><span className="connection-dot" />{connection.path ?? "No connected file"}</div>
          <div className="topbar-actions">
            {saving ? <span className="saving-status">Saving…</span> : null}
            <button className="icon-button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="Toggle theme"><Moon size={18} /></button>
          </div>
        </header>
        {toast ? <div className="toast" role="status" aria-live="polite">{toast}</div> : null}
        <div className="page-scroll" data-keyboard-region="main">{content()}</div>
      </main>

      {editor ? (
        <TransactionEditor
          open
          document={activeDocument}
          type={editor.type}
          transaction={editor.transaction}
          onOpenChange={(open) => { if (!open) setEditor(null); }}
          onSubmit={saveTransaction}
        />
      ) : null}
    </div>
  );
}

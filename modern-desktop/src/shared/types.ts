export type TransactionType = "Expense" | "Income";

export interface FinanceTransaction {
  id?: string;
  date: string;
  amount: number;
  category: string;
  description: string;
  behavior_date?: string;
  [key: string]: unknown;
}

export interface IncomeSource {
  amount: number;
  description: string;
  start_date: string;
  end_date: string | null;
  [key: string]: unknown;
}

export interface FixedCost {
  amount: number;
  desc?: string;
  description?: string;
  start_date: string;
  end_date: string | null;
  [key: string]: unknown;
}

export interface Loan {
  id: string;
  borrower: string;
  amount: number;
  description: string;
  date: string;
  [key: string]: unknown;
}

export interface SavingsGoal {
  name: string;
  target_amount: number;
  allocated_amount: number;
  priority?: "High" | "Medium" | "Low";
  description?: string;
  target_date?: string;
  [key: string]: unknown;
}

export interface AssetSnapshot {
  date: string;
  bank_balance: number;
  wallet_balance: number;
  savings_balance: number;
  investment_balance: number;
  money_lent_balance: number;
  note?: string;
  net_worth: number;
  [key: string]: unknown;
}

export interface BudgetSettings {
  monthly_income?: number | IncomeSource[];
  fixed_costs?: FixedCost[];
  bank_account_balance?: number;
  wallet_balance?: number;
  savings_balance?: number;
  investment_balance?: number;
  money_lent_balance?: number;
  daily_savings_goal?: number;
  category_budgets?: {
    Expense?: Record<string, number>;
    Income?: Record<string, number>;
    [key: string]: unknown;
  };
  loans?: Loan[];
  savings_goals?: SavingsGoal[];
  asset_snapshots?: AssetSnapshot[];
  ai_settings?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface FinanceDocument {
  expenses: FinanceTransaction[];
  incomes: FinanceTransaction[];
  budget_settings: BudgetSettings;
  categories: Record<TransactionType, string[]>;
  [key: string]: unknown;
}

export interface DataConnection {
  path: string | null;
  isConnected: boolean;
  message?: string;
}

export interface DataLoadResult {
  document: FinanceDocument | null;
  connection: DataConnection;
}

export type ReconciliationStatus = "matched" | "possible" | "missing";

export interface BankTransaction {
  id: string;
  date: string;
  amount: number;
  payee: string;
  purpose: string;
  bookingText: string;
  currency: string;
  transactionType: TransactionType;
  suggestedCategory: string;
  status: ReconciliationStatus;
  matchedTransactionId?: string;
  matchConfidence?: "exact" | "fuzzy_date";
}

export interface CsvImportResult {
  transactions: BankTransaction[];
  meta: {
    encoding: string;
    separator: string;
    totalRows: number;
    skippedRows: number;
    message?: string;
  };
}

export interface FinanceApi {
  load(): Promise<DataLoadResult>;
  chooseDataFile(): Promise<DataLoadResult>;
  createDataFile(): Promise<DataLoadResult>;
  saveDocument(document: FinanceDocument): Promise<DataLoadResult>;
  chooseBankCsv(): Promise<CsvImportResult | null>;
  exportText(defaultName: string, text: string): Promise<string | null>;
}

declare global {
  interface Window {
    finance: FinanceApi;
  }
}

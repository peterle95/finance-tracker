import type {
  AssetSnapshot,
  BudgetSettings,
  FinanceDocument,
  FinanceTransaction,
  FixedCost,
  IncomeSource,
  Loan,
  SavingsGoal,
  TransactionType
} from "./types";

export type TransactionDateBasis = "transaction" | "behavior";

export const DEFAULT_EXPENSE_CATEGORIES = [
  "Food",
  "Transportation",
  "Entertainment",
  "Utilities",
  "Shopping",
  "Healthcare",
  "Money Lent",
  "Other"
];

export const DEFAULT_INCOME_CATEGORIES = [
  "Salary",
  "Side Gig",
  "Bonus",
  "Gift",
  "Investment",
  "Other"
];

const PRIORITY_WEIGHT: Record<string, number> = {
  High: 0,
  Medium: 1,
  Low: 2
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function asNumber(value: unknown, fallback = 0): number {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function roundCurrency(value: number): number {
  return Math.round((asNumber(value) + Number.EPSILON) * 100) / 100;
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asDate(value: unknown, fallback: string | null = null): string | null {
  const parsed = asString(value);
  return /^\d{4}-\d{2}-\d{2}$/.test(parsed) ? parsed : fallback;
}

function cloneRecord<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function normalizeTransaction(value: unknown): FinanceTransaction | null {
  if (!isRecord(value)) {
    return null;
  }

  const date = asDate(value.date);
  if (!date) {
    return null;
  }

  return {
    ...value,
    id: value.id === undefined ? undefined : asString(value.id),
    date,
    amount: roundCurrency(asNumber(value.amount)),
    category: asString(value.category, "Other"),
    description: asString(value.description),
    behavior_date: asDate(value.behavior_date) ?? undefined
  };
}

function normalizeTransactions(value: unknown): FinanceTransaction[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map(normalizeTransaction).filter((item): item is FinanceTransaction => item !== null);
}

function normalizeIncomeSource(value: unknown): IncomeSource | null {
  if (!isRecord(value)) {
    return null;
  }
  return {
    ...value,
    amount: roundCurrency(asNumber(value.amount)),
    description: asString(value.description, "Income"),
    start_date: asDate(value.start_date, "2000-01-01") ?? "2000-01-01",
    end_date: asDate(value.end_date)
  };
}

function normalizeFixedCost(value: unknown): FixedCost | null {
  if (!isRecord(value)) {
    return null;
  }
  const description = asString(value.description, asString(value.desc, "Fixed cost"));
  return {
    ...value,
    amount: roundCurrency(asNumber(value.amount)),
    description,
    desc: asString(value.desc, description),
    start_date: asDate(value.start_date, "2000-01-01") ?? "2000-01-01",
    end_date: asDate(value.end_date)
  };
}

function normalizeLoan(value: unknown): Loan | null {
  if (!isRecord(value)) {
    return null;
  }
  return {
    ...value,
    id: asString(value.id),
    borrower: asString(value.borrower, "Unknown"),
    amount: roundCurrency(asNumber(value.amount)),
    description: asString(value.description),
    date: asDate(value.date, "2000-01-01") ?? "2000-01-01"
  };
}

export function moneyLentFromLoans(loans: readonly Pick<Loan, "amount">[]): number {
  return roundCurrency(loans.reduce((total, loan) => total + asNumber(loan.amount), 0));
}

function categoryList(value: unknown, fallback: string[]): string[] {
  if (!Array.isArray(value)) {
    return [...fallback];
  }
  const categories = value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
  return categories.length > 0 ? categories : [...fallback];
}

export function defaultDocument(): FinanceDocument {
  return {
    expenses: [],
    incomes: [],
    budget_settings: {
      fixed_costs: [],
      monthly_income: [],
      bank_account_balance: 0,
      savings_balance: 0,
      investment_balance: 0,
      wallet_balance: 0,
      money_lent_balance: 0,
      daily_savings_goal: 0,
      category_budgets: { Expense: {}, Income: {} },
      loans: [],
      savings_goals: [],
      asset_snapshots: []
    },
    categories: {
      Expense: [...DEFAULT_EXPENSE_CATEGORIES],
      Income: [...DEFAULT_INCOME_CATEGORIES]
    }
  };
}

export function normalizeDocument(raw: unknown): FinanceDocument {
  const root = isRecord(raw) ? raw : {};
  const settings = isRecord(root.budget_settings) ? root.budget_settings : {};
  const sourceCategories = isRecord(root.categories) ? root.categories : {};
  const incomeValue = settings.monthly_income;
  const fixedCosts = Array.isArray(settings.fixed_costs)
    ? settings.fixed_costs.map(normalizeFixedCost).filter((item): item is FixedCost => item !== null)
    : [];
  const loans = Array.isArray(settings.loans)
    ? settings.loans.map(normalizeLoan).filter((item): item is Loan => item !== null)
    : [];
  const storedMoneyLent = roundCurrency(asNumber(settings.money_lent_balance));
  const moneyLentBalance = loans.length ? moneyLentFromLoans(loans) : storedMoneyLent;

  return {
    ...root,
    expenses: normalizeTransactions(root.expenses),
    incomes: normalizeTransactions(root.incomes),
    budget_settings: {
      ...settings,
      fixed_costs: fixedCosts,
      monthly_income: typeof incomeValue === "number"
        ? incomeValue
        : Array.isArray(incomeValue)
          ? incomeValue.map(normalizeIncomeSource).filter((item): item is IncomeSource => item !== null)
          : [],
      bank_account_balance: roundCurrency(asNumber(settings.bank_account_balance)),
      savings_balance: roundCurrency(asNumber(settings.savings_balance)),
      investment_balance: roundCurrency(asNumber(settings.investment_balance)),
      wallet_balance: roundCurrency(asNumber(settings.wallet_balance)),
      money_lent_balance: moneyLentBalance,
      daily_savings_goal: roundCurrency(asNumber(settings.daily_savings_goal)),
      category_budgets: isRecord(settings.category_budgets)
        ? settings.category_budgets as BudgetSettings["category_budgets"]
        : { Expense: {}, Income: {} },
      loans,
      savings_goals: Array.isArray(settings.savings_goals) ? settings.savings_goals : [],
      asset_snapshots: Array.isArray(settings.asset_snapshots) ? settings.asset_snapshots : []
    },
    categories: {
      Expense: categoryList(sourceCategories.Expense, DEFAULT_EXPENSE_CATEGORIES),
      Income: categoryList(sourceCategories.Income, DEFAULT_INCOME_CATEGORIES)
    }
  };
}

export function cloneDocument(document: FinanceDocument): FinanceDocument {
  return cloneRecord(document);
}

export function mergeDocuments(latest: unknown, requested: unknown): FinanceDocument {
  const current = normalizeDocument(latest);
  const update = normalizeDocument(requested);
  return normalizeDocument({
    ...current,
    ...update,
    budget_settings: {
      ...current.budget_settings,
      ...update.budget_settings
    },
    categories: {
      ...current.categories,
      ...update.categories
    }
  });
}

export function isoToday(now = new Date()): string {
  return now.toISOString().slice(0, 10);
}

export function currentMonth(now = new Date()): string {
  return isoToday(now).slice(0, 7);
}

export function monthDays(month: string): number {
  const [year, monthNumber] = month.split("-").map(Number);
  if (!year || !monthNumber) {
    return 30;
  }
  return new Date(year, monthNumber, 0).getDate();
}

export function monthOffset(month: string, offset: number): string {
  const [year, monthNumber] = month.split("-").map(Number);
  const date = new Date(year, monthNumber - 1 + offset, 1, 12);
  return date.toISOString().slice(0, 7);
}

export function nextMonthFirst(date: string): string {
  const source = new Date(date + "T12:00:00");
  source.setMonth(source.getMonth() + 1, 1);
  return source.toISOString().slice(0, 10);
}

function isActiveDuringMonth(entry: { start_date?: unknown; end_date?: unknown }, month: string): boolean {
  const start = asDate(entry.start_date, "2000-01-01") ?? "2000-01-01";
  const end = asDate(entry.end_date);
  const monthStart = month + "-01";
  const monthEnd = month + "-" + String(monthDays(month)).padStart(2, "0");
  return start <= monthEnd && (!end || end >= monthStart);
}

export function getMonthlyIncomeSources(document: FinanceDocument, month: string): IncomeSource[] {
  const value = document.budget_settings.monthly_income;
  if (typeof value === "number") {
    return [{
      amount: value,
      description: "Base Income",
      start_date: "2000-01-01",
      end_date: null
    }];
  }
  return Array.isArray(value)
    ? value.filter((entry) => isActiveDuringMonth(entry, month))
    : [];
}

export function getActiveMonthlyIncome(document: FinanceDocument, month: string): number {
  return getMonthlyIncomeSources(document, month)
    .reduce((total, source) => total + asNumber(source.amount), 0);
}

export function getActiveFixedCosts(document: FinanceDocument, month: string): FixedCost[] {
  const costs = document.budget_settings.fixed_costs;
  return Array.isArray(costs) ? costs.filter((cost) => isActiveDuringMonth(cost, month)) : [];
}

export function sumFixedCosts(document: FinanceDocument, month: string): number {
  return getActiveFixedCosts(document, month).reduce((total, cost) => total + asNumber(cost.amount), 0);
}

function transactionDate(transaction: FinanceTransaction, dateBasis: TransactionDateBasis): string {
  return dateBasis === "behavior" ? transaction.behavior_date ?? transaction.date : transaction.date;
}

export function monthTransactions(
  document: FinanceDocument,
  type: TransactionType,
  month: string,
  dateBasis: TransactionDateBasis = "transaction"
): FinanceTransaction[] {
  const source = type === "Expense" ? document.expenses : document.incomes;
  return source.filter((transaction) => transactionDate(transaction, dateBasis).startsWith(month));
}

export function sumMonthTransactions(document: FinanceDocument, type: TransactionType, month: string): number {
  return monthTransactions(document, type, month)
    .reduce((total, transaction) => total + asNumber(transaction.amount), 0);
}

export function computeNetAvailableForSpending(document: FinanceDocument, month: string): number {
  const baseIncome = getActiveMonthlyIncome(document, month);
  const flexibleIncome = sumMonthTransactions(document, "Income", month);
  const fixedCosts = sumFixedCosts(document, month);
  const savingsGoal = asNumber(document.budget_settings.daily_savings_goal) * monthDays(month);
  return Math.max(baseIncome + flexibleIncome - fixedCosts - savingsGoal, 0);
}

export function monthEndFlexibleBalance(document: FinanceDocument, month: string): number {
  const monthlyBudget = getActiveMonthlyIncome(document, month)
    - sumFixedCosts(document, month)
    - asNumber(document.budget_settings.daily_savings_goal) * monthDays(month);
  return monthlyBudget
    + sumMonthTransactions(document, "Income", month)
    - sumMonthTransactions(document, "Expense", month);
}

export function negativeCarryover(document: FinanceDocument, month: string): number {
  const previous = monthOffset(month, -1);
  const balance = monthEndFlexibleBalance(document, previous);
  return balance < 0 ? balance : 0;
}

export interface DailyBudgetOverview {
  month: string;
  baseIncome: number;
  flexibleIncome: number;
  fixedCosts: number;
  savingsGoal: number;
  carryover: number;
  remainingBudget: number;
  dailyTarget: number;
  spent: number;
  daysRemaining: number;
}

export function dailyBudgetOverview(
  document: FinanceDocument,
  month: string,
  includeNegativeCarryover = false,
  now = new Date(),
  dateBasis: TransactionDateBasis = "transaction"
): DailyBudgetOverview {
  const baseIncome = getActiveMonthlyIncome(document, month);
  const flexibleIncome = sumMonthTransactions(document, "Income", month);
  const fixedCosts = sumFixedCosts(document, month);
  const savingsGoal = asNumber(document.budget_settings.daily_savings_goal) * monthDays(month);
  const carryover = includeNegativeCarryover ? negativeCarryover(document, month) : 0;
  const dayCount = monthDays(month);
  const today = isoToday(now);
  const isCurrent = today.startsWith(month);
  const throughDay = isCurrent ? Number(today.slice(8, 10)) : dayCount;
  let remainingBudget = baseIncome - fixedCosts - savingsGoal + carryover;
  let spent = 0;

  for (let day = 1; day <= throughDay; day += 1) {
    const date = month + "-" + String(day).padStart(2, "0");
    const income = document.incomes
      .filter((item) => transactionDate(item, dateBasis) === date)
      .reduce((total, item) => total + asNumber(item.amount), 0);
    const expense = document.expenses
      .filter((item) => transactionDate(item, dateBasis) === date)
      .reduce((total, item) => total + asNumber(item.amount), 0);
    remainingBudget += income - expense;
    spent += expense;
  }

  const daysRemaining = isCurrent ? dayCount - throughDay + 1 : 0;
  return {
    month,
    baseIncome,
    flexibleIncome,
    fixedCosts,
    savingsGoal,
    carryover,
    remainingBudget,
    dailyTarget: remainingBudget > 0 && daysRemaining > 0 ? remainingBudget / daysRemaining : 0,
    spent,
    daysRemaining
  };
}

export function categoryBudgetPercentages(document: FinanceDocument): Record<string, number> {
  const budgets = document.budget_settings.category_budgets;
  const expense = budgets && isRecord(budgets.Expense) ? budgets.Expense : {};
  return Object.fromEntries(
    Object.entries(expense).map(([category, value]) => [category, asNumber(value)])
  );
}

export interface AutoAssignResult {
  percentages: Record<string, number>;
  message: string;
  isOverspent: boolean;
}

export function autoAssignCategoryBudgets(
  document: FinanceDocument,
  month: string
): AutoAssignResult {
  const categories = document.categories.Expense;
  const available = computeNetAvailableForSpending(document, month);
  if (available <= 0) {
    return { percentages: {}, message: "No flexible budget is available for this month.", isOverspent: false };
  }

  const spendByCategory = Object.fromEntries(categories.map((category) => [category, 0])) as Record<string, number>;
  monthTransactions(document, "Expense", month).forEach((transaction) => {
    if (transaction.category in spendByCategory) {
      spendByCategory[transaction.category] += asNumber(transaction.amount);
    }
  });
  const spent = Object.values(spendByCategory).reduce((total, amount) => total + amount, 0);
  if (spent === 0) {
    return { percentages: {}, message: "Record spending before auto-assigning budgets.", isOverspent: false };
  }

  if (spent <= available) {
    return {
      percentages: Object.fromEntries(categories.map((category) => [
        category,
        (spendByCategory[category] / available) * 100
      ])),
      message: "Budgets now reflect recorded spending; assign the remaining balance where needed.",
      isOverspent: false
    };
  }

  return {
    percentages: Object.fromEntries(categories.map((category) => [
      category,
      (spendByCategory[category] / spent) * 100
    ])),
    message: "Spending exceeds the flexible budget, so percentages follow actual spending.",
    isOverspent: true
  };
}

export function getGoals(document: FinanceDocument): SavingsGoal[] {
  const source = document.budget_settings.savings_goals;
  if (!Array.isArray(source)) {
    return [];
  }
  return source.filter(isRecord).map((goal) => ({
    ...goal,
    name: asString(goal.name, "Untitled goal"),
    target_amount: asNumber(goal.target_amount),
    allocated_amount: asNumber(goal.allocated_amount),
    priority: ["High", "Medium", "Low"].includes(asString(goal.priority))
      ? asString(goal.priority) as SavingsGoal["priority"]
      : "Medium"
  }));
}

export function goalSummary(document: FinanceDocument) {
  const goals = getGoals(document);
  const totalSavings = asNumber(document.budget_settings.savings_balance);
  const allocated = goals.reduce((total, goal) => total + goal.allocated_amount, 0);
  return {
    totalGoals: goals.length,
    activeGoals: goals.filter((goal) => goal.allocated_amount < goal.target_amount).length,
    completedGoals: goals.filter((goal) => goal.allocated_amount >= goal.target_amount).length,
    totalSavings,
    allocated,
    unallocated: Math.max(totalSavings - allocated, 0)
  };
}

export function autoDistributeGoals(document: FinanceDocument): SavingsGoal[] {
  const goals = cloneRecord(getGoals(document));
  let available = goalSummary(document).unallocated;
  goals
    .filter((goal) => goal.allocated_amount < goal.target_amount)
    .sort((first, second) => {
      const priority = PRIORITY_WEIGHT[first.priority ?? "Medium"] - PRIORITY_WEIGHT[second.priority ?? "Medium"];
      return priority || (first.target_amount - first.allocated_amount) - (second.target_amount - second.allocated_amount);
    })
    .forEach((goal) => {
      const need = Math.max(goal.target_amount - goal.allocated_amount, 0);
      const allocation = Math.min(need, available);
      goal.allocated_amount += allocation;
      available -= allocation;
    });
  return goals;
}

export function netWorth(document: FinanceDocument): number {
  const settings = document.budget_settings;
  return roundCurrency(asNumber(settings.bank_account_balance)
    + asNumber(settings.wallet_balance)
    + asNumber(settings.savings_balance)
    + asNumber(settings.investment_balance)
    + asNumber(settings.money_lent_balance));
}

export interface AssetAllocationItem {
  name: string;
  value: number;
}

export function assetAllocation(document: FinanceDocument): {
  assets: AssetAllocationItem[];
  liabilities: AssetAllocationItem[];
} {
  const settings = document.budget_settings;
  const moneyLent = roundCurrency(asNumber(settings.money_lent_balance));
  const balances = [
    { name: "Bank", value: roundCurrency(asNumber(settings.bank_account_balance)) },
    { name: "Wallet", value: roundCurrency(asNumber(settings.wallet_balance)) },
    { name: "Savings", value: roundCurrency(asNumber(settings.savings_balance)) },
    { name: "Investments", value: roundCurrency(asNumber(settings.investment_balance)) },
    { name: moneyLent >= 0 ? "Money lent" : "Money owed", value: moneyLent }
  ].filter((item) => Number.isFinite(item.value) && item.value !== 0);

  return {
    assets: balances.filter((item) => item.value > 0),
    liabilities: balances.filter((item) => item.value < 0)
  };
}

export function snapshots(document: FinanceDocument): AssetSnapshot[] {
  const source = document.budget_settings.asset_snapshots;
  if (!Array.isArray(source)) {
    return [];
  }
  return source
    .filter(isRecord)
    .map((snapshot) => ({
      ...snapshot,
      date: asDate(snapshot.date, isoToday()) ?? isoToday(),
      bank_balance: roundCurrency(asNumber(snapshot.bank_balance)),
      wallet_balance: roundCurrency(asNumber(snapshot.wallet_balance)),
      savings_balance: roundCurrency(asNumber(snapshot.savings_balance)),
      investment_balance: roundCurrency(asNumber(snapshot.investment_balance)),
      money_lent_balance: roundCurrency(asNumber(snapshot.money_lent_balance)),
      net_worth: roundCurrency(asNumber(snapshot.net_worth))
    }))
    .sort((first, second) => first.date.localeCompare(second.date));
}

export function createSnapshot(document: FinanceDocument, date = isoToday(), note = ""): AssetSnapshot {
  const settings = document.budget_settings;
  return {
    date,
    bank_balance: roundCurrency(asNumber(settings.bank_account_balance)),
    wallet_balance: roundCurrency(asNumber(settings.wallet_balance)),
    savings_balance: roundCurrency(asNumber(settings.savings_balance)),
    investment_balance: roundCurrency(asNumber(settings.investment_balance)),
    money_lent_balance: roundCurrency(asNumber(settings.money_lent_balance)),
    note,
    net_worth: netWorth(document)
  };
}

export function projection(document: FinanceDocument, months: number, startMonth = currentMonth()) {
  const rows: Array<{ month: string; change: number; balance: number; savingsTarget: number }> = [];
  let balance = netWorth(document);
  for (let offset = 0; offset < months; offset += 1) {
    const month = monthOffset(startMonth, offset);
    const savingsTarget = asNumber(document.budget_settings.daily_savings_goal) * monthDays(month);
    balance += savingsTarget;
    rows.push({ month, change: savingsTarget, balance, savingsTarget });
  }
  return rows;
}

export function categoryTotals(
  document: FinanceDocument,
  type: TransactionType,
  startMonth: string,
  endMonth = startMonth,
  includeRecurring = true,
  dateBasis: TransactionDateBasis = "transaction"
): Array<{ name: string; value: number }> {
  const totals = new Map<string, number>();
  let month = startMonth;
  while (month <= endMonth) {
    monthTransactions(document, type, month, dateBasis).forEach((transaction) => {
      totals.set(transaction.category, (totals.get(transaction.category) ?? 0) + asNumber(transaction.amount));
    });
    if (includeRecurring && type === "Expense") {
      const recurring = sumFixedCosts(document, month);
      if (recurring > 0) {
        totals.set("Fixed Costs", (totals.get("Fixed Costs") ?? 0) + recurring);
      }
    }
    if (includeRecurring && type === "Income") {
      const recurring = getActiveMonthlyIncome(document, month);
      if (recurring > 0) {
        totals.set("Base Income", (totals.get("Base Income") ?? 0) + recurring);
      }
    }
    month = monthOffset(month, 1);
  }
  return [...totals.entries()]
    .map(([name, value]) => ({ name, value }))
    .sort((first, second) => second.value - first.value);
}

export function historicalTotals(
  document: FinanceDocument,
  type: TransactionType,
  months = 6,
  end = currentMonth(),
  dateBasis: TransactionDateBasis = "transaction"
) {
  return Array.from({ length: months }, (_, index) => {
    const month = monthOffset(end, index - months + 1);
    const transactions = monthTransactions(document, type, month, dateBasis)
      .reduce((total, transaction) => total + asNumber(transaction.amount), 0);
    const recurring = type === "Expense" ? sumFixedCosts(document, month) : getActiveMonthlyIncome(document, month);
    return { month, value: transactions + recurring };
  });
}

export function spendingPace(
  document: FinanceDocument,
  month: string,
  dateBasis: TransactionDateBasis = "transaction"
) {
  const overview = dailyBudgetOverview(document, month, false, new Date(), dateBasis);
  return {
    ...overview,
    flexibleBudget: computeNetAvailableForSpending(document, month),
    status: overview.remainingBudget <= 0
      ? "Budget depleted"
      : overview.dailyTarget === 0
        ? "Month complete"
        : "On track"
  };
}

export function dayOfWeekHeatmap(
  document: FinanceDocument,
  months = 3,
  end = currentMonth(),
  dateBasis: TransactionDateBasis = "transaction"
) {
  const values = Array.from({ length: 7 }, (_, day) => ({ day, value: 0 }));
  for (let offset = 0; offset < months; offset += 1) {
    const month = monthOffset(end, -offset);
    monthTransactions(document, "Expense", month, dateBasis).forEach((transaction) => {
      const date = new Date(transactionDate(transaction, dateBasis) + "T12:00:00");
      if (!Number.isNaN(date.getTime())) {
        values[date.getDay()].value += asNumber(transaction.amount);
      }
    });
  }
  return values;
}

export function makeTransaction(
  type: TransactionType,
  values: {
    date: string;
    amount: number;
    category: string;
    description: string;
    behavior_date?: string;
    [key: string]: unknown;
  },
  bnpl = false
): FinanceTransaction {
  const id = typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : String(Date.now()) + "-" + String(Math.random()).slice(2);
  const date = bnpl ? nextMonthFirst(values.date) : values.date;
  return {
    ...values,
    id,
    date,
    amount: roundCurrency(asNumber(values.amount)),
    behavior_date: bnpl ? values.date : values.behavior_date
  };
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 2
  }).format(value);
}

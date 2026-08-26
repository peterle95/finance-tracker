import { randomUUID } from "node:crypto";
import { access, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { isDeepStrictEqual } from "node:util";
import type { BrowserWindow, OpenDialogOptions, SaveDialogOptions } from "electron";
import { dialog } from "electron";
import { defaultDocument, normalizeDocument } from "../shared/finance";
import { parseBankCsvText } from "../shared/reconciliation";
import type {
  BudgetSettings,
  CsvImportResult,
  DataLoadResult,
  FinanceDocument,
  FinanceTransaction,
  TransactionType
} from "../shared/types";
import { writeJsonAtomically } from "./file-utils";

interface LocalConfig {
  dataDirectory?: string;
  dataFile?: string;
}

interface CategoryRecord {
  name: string;
  file_key: string;
  [key: string]: unknown;
}

interface CategoriesFile {
  Expense: CategoryRecord[];
  Income: CategoryRecord[];
  [key: string]: unknown;
}

const BUDGET_KEYS = ["monthly_income", "fixed_costs", "daily_savings_goal", "category_budgets"] as const;
const NET_WORTH_KEYS = [
  "bank_account_balance",
  "cash_balance",
  "wallet_balance",
  "savings_balance",
  "investment_balance",
  "money_lent_balance",
  "asset_snapshots"
] as const;
const PREFERENCE_KEYS = ["ai_settings", "default_behaviors", "default_ranges", "defaultNetWorthPeriod", "defaultNetWorthBreakdownPeriod"] as const;

async function exists(filePath: string): Promise<boolean> {
  try {
    await access(filePath);
    return true;
  } catch {
    return false;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function equal(left: unknown, right: unknown): boolean {
  if (left === undefined || right === undefined) return left === right;
  return isDeepStrictEqual(JSON.parse(JSON.stringify(left)), JSON.parse(JSON.stringify(right)));
}

function decodeCsv(buffer: Buffer): string {
  const utf8 = buffer.toString("utf8");
  return utf8.includes("\uFFFD") ? buffer.toString("latin1") : utf8;
}

function slug(name: string, used: Set<string>): string {
  const base = name.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "category";
  let key = base;
  let suffix = 2;
  while (used.has(key)) {
    key = base + "-" + suffix;
    suffix += 1;
  }
  used.add(key);
  return key;
}

function transactionFile(type: TransactionType, key: string): string {
  return `transactions_${type.toLowerCase()}_${key}.json`;
}

function transactions(document: FinanceDocument, type: TransactionType): FinanceTransaction[] {
  return type === "Expense" ? document.expenses : document.incomes;
}

function onlyCategoryRenames(
  before: FinanceTransaction[],
  after: FinanceTransaction[],
  oldNames: string[],
  newNames: string[]
): boolean {
  if (before.length !== after.length) return false;
  const renamed = new Map(oldNames.map((name, index) => [name, newNames[index] ?? name]));
  return equal(before.map((item) => ({ ...item, category: renamed.get(item.category) ?? item.category })), after);
}

function withTransactionIds(items: FinanceTransaction[]): FinanceTransaction[] {
  return items.map((item) => item.id ? item : { ...item, id: randomUUID() });
}

function categoryRecords(document: FinanceDocument): CategoriesFile {
  return {
    Expense: makeRecords(document.categories.Expense),
    Income: makeRecords(document.categories.Income)
  };
}

function makeRecords(names: string[]): CategoryRecord[] {
  const used = new Set<string>();
  return names.map((name) => ({ name, file_key: slug(name, used) }));
}

function extras(settings: BudgetSettings): Record<string, unknown> {
  const owned = new Set<string>([...BUDGET_KEYS, ...NET_WORTH_KEYS, ...PREFERENCE_KEYS, "loans", "savings_goals"]);
  return Object.fromEntries(Object.entries(settings).filter(([key]) => !owned.has(key)));
}

export class DataStore {
  private selectedPath: string | null = null;
  private categories: CategoriesFile | null = null;
  private saveQueue: Promise<void> = Promise.resolve();

  public constructor(
    private readonly configPath: string,
    private readonly developmentDefault: string | null
  ) {}

  public async load(): Promise<DataLoadResult> {
    const dataPath = await this.resolveDataPath();
    if (!dataPath) {
      return {
        document: null,
        connection: {
          path: null,
          isConnected: false,
          message: "Choose your shared finance data directory to begin."
        }
      };
    }

    try {
      if (!await exists(join(dataPath, "categories.json"))) {
        const legacyPath = join(dataPath, "finance_data.json");
        if (await exists(legacyPath)) {
          await this.migrate(dataPath, legacyPath);
        } else {
          if ((await readdir(dataPath)).some((name) => name.endsWith(".json"))) {
            throw new Error("categories.json is missing from a non-empty finance data directory.");
          }
          await this.writeNewDirectory(dataPath, defaultDocument());
        }
      }
      const result = await this.readDirectory(dataPath);
      return {
        document: result.document,
        warnings: result.warnings,
        connection: { path: dataPath, isConnected: true }
      };
    } catch (error) {
      return {
        document: null,
        connection: {
          path: dataPath,
          isConnected: false,
          message: error instanceof Error ? error.message : "The finance data directory could not be read."
        }
      };
    }
  }

  public async chooseDataFile(parent?: BrowserWindow): Promise<DataLoadResult> {
    const result = await this.showDirectoryDialog("Connect finance data directory", parent);
    if (!result.canceled && result.filePaths[0]) {
      await this.setSelectedPath(result.filePaths[0]);
    }
    return this.load();
  }

  public async createDataFile(parent?: BrowserWindow): Promise<DataLoadResult> {
    const result = await this.showDirectoryDialog("Create finance data directory", parent);
    if (!result.canceled && result.filePaths[0]) {
      await this.setSelectedPath(result.filePaths[0]);
    }
    return this.load();
  }

  public async saveDocument(previous: FinanceDocument, requested: FinanceDocument): Promise<DataLoadResult> {
    const operation = this.saveQueue.then(() => this.saveDocumentNow(previous, requested));
    this.saveQueue = operation.then(() => undefined, () => undefined);
    return operation;
  }

  private async saveDocumentNow(previous: FinanceDocument, requested: FinanceDocument): Promise<DataLoadResult> {
    const dataPath = await this.resolveDataPath();
    if (!dataPath || !this.categories) {
      throw new Error("Choose a finance data directory before saving.");
    }

    const categoryTypes = (["Expense", "Income"] as const)
      .filter((type) => !equal(previous.categories[type], requested.categories[type]));
    for (const type of categoryTypes) {
      if (!equal(transactions(previous, type), transactions(requested, type))
          && !onlyCategoryRenames(transactions(previous, type), transactions(requested, type),
            previous.categories[type], requested.categories[type])) {
        throw new Error(`Save ${type.toLowerCase()} category and transaction changes separately.`);
      }
    }
    for (const type of categoryTypes) {
      await this.saveCategoryChanges(dataPath, type, previous, requested);
    }

    await this.saveTransactions(dataPath, previous, requested, new Set(categoryTypes));
    await this.saveObjectChanges(dataPath, "budget.json", previous.budget_settings, requested.budget_settings, BUDGET_KEYS);
    await this.saveObjectChanges(dataPath, "net_worth.json", previous.budget_settings, requested.budget_settings, NET_WORTH_KEYS);
    await this.saveObjectChanges(dataPath, "preferences.json", previous.budget_settings, requested.budget_settings, PREFERENCE_KEYS);
    await this.saveArrayChange(dataPath, "loans.json", previous.budget_settings.loans, requested.budget_settings.loans);
    await this.saveArrayChange(dataPath, "savings_goals.json", previous.budget_settings.savings_goals, requested.budget_settings.savings_goals);

    const result = await this.readDirectory(dataPath);
    return { ...result, connection: { path: dataPath, isConnected: true } };
  }

  public async chooseBankCsv(parent?: BrowserWindow): Promise<CsvImportResult | null> {
    const options: OpenDialogOptions = {
      title: "Import bank CSV",
      properties: ["openFile"],
      filters: [{ name: "CSV files", extensions: ["csv", "txt"] }]
    };
    const result = parent ? await dialog.showOpenDialog(parent, options) : await dialog.showOpenDialog(options);
    if (result.canceled || !result.filePaths[0]) {
      return null;
    }
    return parseBankCsvText(decodeCsv(await readFile(result.filePaths[0])));
  }

  public async exportText(defaultName: string, text: string, parent?: BrowserWindow): Promise<string | null> {
    const options: SaveDialogOptions = {
      title: "Export report",
      defaultPath: defaultName,
      filters: [{ name: "Text file", extensions: ["txt"] }]
    };
    const result = parent ? await dialog.showSaveDialog(parent, options) : await dialog.showSaveDialog(options);
    if (result.canceled || !result.filePath) {
      return null;
    }
    await writeFile(result.filePath, text, "utf8");
    return result.filePath;
  }

  private async showDirectoryDialog(title: string, parent?: BrowserWindow) {
    const options: OpenDialogOptions = { title, properties: ["openDirectory", "createDirectory"] };
    return parent ? dialog.showOpenDialog(parent, options) : dialog.showOpenDialog(options);
  }

  private async migrate(dataPath: string, legacyPath: string): Promise<void> {
    const raw = await this.readJson(legacyPath);
    if (!isRecord(raw)) {
      throw new Error("The legacy finance_data.json must contain a JSON object.");
    }
    const document = normalizeDocument(raw);
    document.expenses = withTransactionIds(document.expenses);
    document.incomes = withTransactionIds(document.incomes);
    for (const type of ["Expense", "Income"] as const) {
      document.categories[type] = [...new Set([
        ...document.categories[type],
        ...transactions(document, type).map((item) => item.category)
      ])];
    }
    await this.writeNewDirectory(dataPath, document);
    const reconstructed = (await this.readDirectory(dataPath)).document;
    if (!equal(reconstructed, normalizeDocument(document))) {
      await rm(join(dataPath, "categories.json"), { force: true });
      throw new Error("Migration verification failed; finance_data.json was left untouched.");
    }
  }

  private async writeNewDirectory(dataPath: string, document: FinanceDocument): Promise<void> {
    const categories = categoryRecords(document);
    const settings = document.budget_settings;
    for (const type of ["Expense", "Income"] as const) {
      for (const category of categories[type]) {
        await writeJsonAtomically(join(dataPath, transactionFile(type, category.file_key)),
          withTransactionIds(transactions(document, type).filter((item) => item.category === category.name)));
      }
    }
    await writeJsonAtomically(join(dataPath, "budget.json"), Object.fromEntries(BUDGET_KEYS.map((key) => [key, settings[key]])));
    await writeJsonAtomically(join(dataPath, "net_worth.json"), Object.fromEntries(NET_WORTH_KEYS.map((key) => [key, settings[key]])));
    await writeJsonAtomically(join(dataPath, "loans.json"), settings.loans ?? []);
    await writeJsonAtomically(join(dataPath, "savings_goals.json"), settings.savings_goals ?? []);
    await writeJsonAtomically(join(dataPath, "preferences.json"), {
      ...Object.fromEntries(PREFERENCE_KEYS.map((key) => [key, settings[key]])),
      _extra: {
        legacy_budget_settings: extras(settings),
        legacy_root: Object.fromEntries(Object.entries(document).filter(([key]) => !["expenses", "incomes", "budget_settings", "categories"].includes(key)))
      }
    });
    await writeJsonAtomically(join(dataPath, "categories.json"), categories);
    this.categories = categories;
  }

  private async readDirectory(dataPath: string): Promise<{ document: FinanceDocument; warnings: string[] }> {
    const categoriesRaw = await this.readJson(join(dataPath, "categories.json"));
    if (!isRecord(categoriesRaw)) {
      throw new Error("categories.json must contain a JSON object.");
    }
    const categories = this.parseCategories(categoriesRaw);
    const [budget, netWorth, loans, goals, preferences] = await Promise.all([
      this.readObject(join(dataPath, "budget.json")),
      this.readObject(join(dataPath, "net_worth.json")),
      this.readArray(join(dataPath, "loans.json")),
      this.readArray(join(dataPath, "savings_goals.json")),
      this.readObject(join(dataPath, "preferences.json"))
    ]);
    const extra = isRecord(preferences._extra) ? preferences._extra : {};
    const budgetExtra = {
      ...(isRecord(extra.budget_settings) ? extra.budget_settings : {}),
      ...(isRecord(extra.legacy_budget_settings) ? extra.legacy_budget_settings : {})
    };
    const documentExtra = {
      ...(isRecord(extra.document) ? extra.document : {}),
      ...(isRecord(extra.legacy_root) ? extra.legacy_root : {})
    };
    const { _extra: budgetExtraRaw, ...budgetFields } = budget;
    const { _extra: netWorthExtraRaw, ...netWorthFields } = netWorth;
    const document = normalizeDocument({
      ...documentExtra,
      expenses: await this.readCategoryTransactions(dataPath, "Expense", categories.Expense),
      incomes: await this.readCategoryTransactions(dataPath, "Income", categories.Income),
      categories: {
        Expense: categories.Expense.map((item) => item.name),
        Income: categories.Income.map((item) => item.name)
      },
      budget_settings: { ...budgetExtra,
        ...(isRecord(budgetExtraRaw) ? budgetExtraRaw : {}), ...budgetFields,
        ...(isRecord(netWorthExtraRaw) ? netWorthExtraRaw : {}), ...netWorthFields,
        loans, savings_goals: goals,
        ...Object.fromEntries(PREFERENCE_KEYS.map((key) => [key, preferences[key]])) }
    });
    this.categories = categories;
    return { document, warnings: await this.findWarnings(dataPath, categories) };
  }

  private parseCategories(raw: Record<string, unknown>): CategoriesFile {
    const parse = (value: unknown, type: TransactionType): CategoryRecord[] => {
      if (!Array.isArray(value)) {
        throw new Error(`categories.json ${type} must be an array.`);
      }
      return value.map((item) => {
        if (!isRecord(item) || typeof item.name !== "string" || typeof item.file_key !== "string") {
          throw new Error(`categories.json ${type} entries require name and file_key.`);
        }
        if (!item.name.trim() || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.file_key)) {
          throw new Error(`categories.json ${type} entries have an invalid name or file_key.`);
        }
        return { ...item, name: item.name, file_key: item.file_key };
      });
    };
    const categories = { ...raw, Expense: parse(raw.Expense, "Expense"), Income: parse(raw.Income, "Income") };
    for (const type of ["Expense", "Income"] as const) {
      if (new Set(categories[type].map((item) => item.name.toLowerCase())).size !== categories[type].length
          || new Set(categories[type].map((item) => item.file_key)).size !== categories[type].length) {
        throw new Error(`categories.json ${type} names and file_key values must be unique.`);
      }
    }
    return categories;
  }

  private async readCategoryTransactions(dataPath: string, type: TransactionType, records: CategoryRecord[]) {
    const result: FinanceTransaction[] = [];
    for (const category of records) {
      const path = join(dataPath, transactionFile(type, category.file_key));
      if (!await exists(path)) await writeJsonAtomically(path, []);
      const items = await this.readArray(path);
      if (!items.every(isRecord)) throw new Error(`${transactionFile(type, category.file_key)} must contain transaction objects.`);
      result.push(...withTransactionIds(items.map((item) => ({ ...item, category: category.name })) as FinanceTransaction[]));
    }
    return result;
  }

  private async findWarnings(dataPath: string, categories: CategoriesFile): Promise<string[]> {
    const names = await readdir(dataPath);
    const warnings = names.filter((name) => /conflict/i.test(name)).map((name) => `Ignored conflict file: ${name}`);
    const known = new Set(((["Expense", "Income"] as const).flatMap((type) =>
      categories[type].map((category) => transactionFile(type, category.file_key)))));
    for (const name of names.filter((item) => !/conflict/i.test(item) && /^transactions_(expense|income)_.+\.json$/.test(item))) {
      if (!known.has(name)) {
        warnings.push(`Orphan transaction file: ${name}`);
      }
    }
    return warnings;
  }

  private async saveCategoryChanges(
    dataPath: string,
    type: TransactionType,
    previous: FinanceDocument,
    requested: FinanceDocument
  ): Promise<void> {
    const records = this.categories![type];
    const oldNames = previous.categories[type];
    const newNames = requested.categories[type];
    const removed = oldNames.filter((name) => !newNames.includes(name));
    const added = newNames.filter((name) => !oldNames.includes(name));

    const positionalRename = removed.length === added.length && removed.every((name) => {
      const replacement = newNames[oldNames.indexOf(name)];
      return added.includes(replacement);
    });
    if (positionalRename) {
      for (const oldName of removed) {
        const replacement = newNames[oldNames.indexOf(oldName)];
        const record = records.find((item) => item.name === oldName);
        if (record) {
          const items = await this.readArray(join(dataPath, transactionFile(type, record.file_key)));
          await writeJsonAtomically(join(dataPath, transactionFile(type, record.file_key)),
            items.map((item) => isRecord(item) ? { ...item, category: replacement } : item));
          record.name = replacement;
        }
      }
    } else {
      for (const name of removed) {
        const index = records.findIndex((item) => item.name === name);
        if (index < 0) continue;
        const path = join(dataPath, transactionFile(type, records[index].file_key));
        if ((await this.readArray(path)).length) {
          throw new Error(`Cannot delete category "${name}" because it has transactions.`);
        }
        await rm(path, { force: true });
        records.splice(index, 1);
      }
      const used = new Set(records.map((item) => item.file_key));
      for (const name of added) {
        const record = { name, file_key: slug(name, used) };
        records.push(record);
        await writeJsonAtomically(join(dataPath, transactionFile(type, record.file_key)), []);
      }
    }
    const order = new Map(newNames.map((name, index) => [name, index]));
    records.sort((left, right) => (order.get(left.name) ?? Infinity) - (order.get(right.name) ?? Infinity));
    await writeJsonAtomically(join(dataPath, "categories.json"), this.categories);
  }

  private async saveTransactions(dataPath: string, previous: FinanceDocument, requested: FinanceDocument, renamedTypes: Set<TransactionType>) {
    for (const type of ["Expense", "Income"] as const) {
      if (renamedTypes.has(type)) continue;
      const before = transactions(previous, type);
      const after = transactions(requested, type);
      if (equal(before, after)) continue;
      const changedCategories = new Set<string>();
      const beforeById = new Map(before.map((item) => [item.id, item]));
      const afterById = new Map(after.map((item) => [item.id, item]));
      for (const [id, item] of beforeById) if (!equal(item, afterById.get(id))) changedCategories.add(item.category);
      for (const [id, item] of afterById) if (!equal(item, beforeById.get(id))) changedCategories.add(item.category);
      for (const category of changedCategories) {
        const record = this.categories![type].find((item) => item.name === category);
        if (!record) throw new Error(`Unknown ${type.toLowerCase()} category "${category}".`);
        const path = join(dataPath, transactionFile(type, record.file_key));
        const latestRows = await this.readArray(path);
        if (!latestRows.every(isRecord)) throw new Error(`${transactionFile(type, record.file_key)} must contain transaction objects.`);
        const latest = latestRows as FinanceTransaction[];
        const removedIds = new Set(before.filter((item) => item.category === category && afterById.get(item.id)?.category !== category).map((item) => item.id));
        const changed = new Map(after.filter((item) => item.category === category && !equal(item, beforeById.get(item.id)))
          .map((item) => [item.id, item]));
        const merged = latest.filter((item) => !removedIds.has(item.id)).map((item) => changed.get(item.id) ?? item);
        const latestIds = new Set(latest.map((item) => item.id));
        merged.push(...after.filter((item) => item.category === category && !latestIds.has(item.id)
          && beforeById.get(item.id)?.category !== category));
        await writeJsonAtomically(path, merged);
      }
    }
  }

  private async saveObjectChanges(
    dataPath: string,
    fileName: string,
    previous: BudgetSettings,
    requested: BudgetSettings,
    keys: readonly string[]
  ) {
    const changed = keys.filter((key) => !equal(previous[key], requested[key]));
    if (!changed.length) return;
    const latest = await this.readObject(join(dataPath, fileName));
    for (const key of changed) latest[key] = requested[key];
    await writeJsonAtomically(join(dataPath, fileName), latest);
  }

  private async saveArrayChange(dataPath: string, fileName: string, previous: unknown, requested: unknown) {
    if (!equal(previous, requested)) await writeJsonAtomically(join(dataPath, fileName), requested ?? []);
  }

  private async resolveDataPath(): Promise<string | null> {
    if (this.selectedPath && await exists(this.selectedPath)) {
      const normalized = await this.normalizeDataPath(this.selectedPath);
      if (normalized !== this.selectedPath) await this.setSelectedPath(normalized);
      return normalized;
    }
    const config = await this.readConfig();
    const configured = config.dataDirectory ?? (config.dataFile ? dirname(config.dataFile) : null);
    if (configured && await exists(configured)) {
      const normalized = await this.normalizeDataPath(configured);
      if (normalized !== resolve(configured)) await this.setSelectedPath(normalized);
      else this.selectedPath = normalized;
      return normalized;
    }
    const environmentPath = process.env.FINANCE_DATA_DIR
      ?? (process.env.FINANCE_DATA_FILE && await exists(process.env.FINANCE_DATA_FILE)
        ? dirname(process.env.FINANCE_DATA_FILE) : null);
    if (environmentPath && await exists(environmentPath)) {
      const normalized = await this.normalizeDataPath(environmentPath);
      await this.setSelectedPath(normalized);
      return normalized;
    }
    if (this.developmentDefault && await exists(this.developmentDefault)) {
      await this.setSelectedPath(this.developmentDefault);
      return resolve(this.developmentDefault);
    }
    return null;
  }

  private async normalizeDataPath(dataPath: string): Promise<string> {
    const normalized = resolve(dataPath);
    const shared = join(normalized, "shared");
    return !await exists(join(normalized, "categories.json")) && await exists(join(shared, "categories.json"))
      ? shared
      : normalized;
  }

  private async readJson(filePath: string): Promise<unknown> {
    try {
      return JSON.parse(await readFile(filePath, "utf8"));
    } catch (error) {
      if (error instanceof SyntaxError) throw new Error(`${filePath.split(/[\\/]/).at(-1)} is not valid JSON.`);
      throw error;
    }
  }

  private async readObject(filePath: string): Promise<Record<string, unknown>> {
    const value = await this.readJson(filePath);
    if (!isRecord(value)) throw new Error(`${filePath.split(/[\\/]/).at(-1)} must contain a JSON object.`);
    return value;
  }

  private async readArray(filePath: string): Promise<unknown[]> {
    const value = await this.readJson(filePath);
    if (!Array.isArray(value)) throw new Error(`${filePath.split(/[\\/]/).at(-1)} must contain a JSON array.`);
    return value;
  }

  private async setSelectedPath(dataPath: string): Promise<void> {
    this.selectedPath = resolve(dataPath);
    await writeJsonAtomically(this.configPath, { dataDirectory: this.selectedPath });
  }

  private async readConfig(): Promise<LocalConfig> {
    try {
      const parsed: unknown = JSON.parse(await readFile(this.configPath, "utf8"));
      return isRecord(parsed) ? parsed : {};
    } catch {
      return {};
    }
  }
}

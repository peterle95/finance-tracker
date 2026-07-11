import { access, readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import type { BrowserWindow, OpenDialogOptions, SaveDialogOptions } from "electron";
import { dialog } from "electron";
import { defaultDocument, mergeDocuments, normalizeDocument } from "../shared/finance";
import { parseBankCsvText } from "../shared/reconciliation";
import type { CsvImportResult, DataLoadResult, FinanceDocument } from "../shared/types";
import { writeJsonAtomically } from "./file-utils";

interface LocalConfig {
  dataFile?: string;
}

async function exists(filePath: string): Promise<boolean> {
  try {
    await access(filePath);
    return true;
  } catch {
    return false;
  }
}

function decodeCsv(buffer: Buffer): string {
  const utf8 = buffer.toString("utf8");
  return utf8.includes("\uFFFD") ? buffer.toString("latin1") : utf8;
}

export class DataStore {
  private selectedPath: string | null = null;

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
          message: "Choose your shared finance_data.json file to begin."
        }
      };
    }

    try {
      const document = await this.readDocument(dataPath);
      return {
        document,
        connection: {
          path: dataPath,
          isConnected: true
        }
      };
    } catch (error) {
      return {
        document: null,
        connection: {
          path: dataPath,
          isConnected: false,
          message: error instanceof Error ? error.message : "The finance data file could not be read."
        }
      };
    }
  }

  public async chooseDataFile(parent?: BrowserWindow): Promise<DataLoadResult> {
    const options: OpenDialogOptions = {
      title: "Connect finance_data.json",
      properties: ["openFile"],
      filters: [{ name: "Finance data", extensions: ["json"] }]
    };
    const result = parent
      ? await dialog.showOpenDialog(parent, options)
      : await dialog.showOpenDialog(options);
    if (!result.canceled && result.filePaths[0]) {
      await this.setSelectedPath(result.filePaths[0]);
    }
    return this.load();
  }

  public async createDataFile(parent?: BrowserWindow): Promise<DataLoadResult> {
    const options: SaveDialogOptions = {
      title: "Create finance_data.json",
      defaultPath: "finance_data.json",
      filters: [{ name: "Finance data", extensions: ["json"] }]
    };
    const result = parent
      ? await dialog.showSaveDialog(parent, options)
      : await dialog.showSaveDialog(options);
    if (!result.canceled && result.filePath) {
      await writeJsonAtomically(result.filePath, defaultDocument());
      await this.setSelectedPath(result.filePath);
    }
    return this.load();
  }

  public async saveDocument(document: FinanceDocument): Promise<DataLoadResult> {
    const dataPath = await this.resolveDataPath();
    if (!dataPath) {
      throw new Error("Choose a finance_data.json file before saving.");
    }

    const latest = await this.readDocument(dataPath);
    const merged = mergeDocuments(latest, document);
    await writeJsonAtomically(dataPath, merged);
    return {
      document: merged,
      connection: {
        path: dataPath,
        isConnected: true
      }
    };
  }

  public async chooseBankCsv(parent?: BrowserWindow): Promise<CsvImportResult | null> {
    const options: OpenDialogOptions = {
      title: "Import bank CSV",
      properties: ["openFile"],
      filters: [{ name: "CSV files", extensions: ["csv", "txt"] }]
    };
    const result = parent
      ? await dialog.showOpenDialog(parent, options)
      : await dialog.showOpenDialog(options);
    if (result.canceled || !result.filePaths[0]) {
      return null;
    }
    const content = await readFile(result.filePaths[0]);
    return parseBankCsvText(decodeCsv(content));
  }

  public async exportText(defaultName: string, text: string, parent?: BrowserWindow): Promise<string | null> {
    const options: SaveDialogOptions = {
      title: "Export report",
      defaultPath: defaultName,
      filters: [{ name: "Text file", extensions: ["txt"] }]
    };
    const result = parent
      ? await dialog.showSaveDialog(parent, options)
      : await dialog.showSaveDialog(options);
    if (result.canceled || !result.filePath) {
      return null;
    }
    await writeFile(result.filePath, text, "utf8");
    return result.filePath;
  }

  private async resolveDataPath(): Promise<string | null> {
    if (this.selectedPath && await exists(this.selectedPath)) {
      return this.selectedPath;
    }

    const config = await this.readConfig();
    if (config.dataFile && await exists(config.dataFile)) {
      this.selectedPath = config.dataFile;
      return this.selectedPath;
    }

    const environmentPath = process.env.FINANCE_DATA_FILE;
    if (environmentPath && await exists(environmentPath)) {
      await this.setSelectedPath(environmentPath);
      return environmentPath;
    }

    if (this.developmentDefault && await exists(this.developmentDefault)) {
      await this.setSelectedPath(this.developmentDefault);
      return this.developmentDefault;
    }

    return null;
  }

  private async readDocument(dataPath: string): Promise<FinanceDocument> {
    const text = await readFile(dataPath, "utf8");
    let raw: unknown;
    try {
      raw = JSON.parse(text);
    } catch {
      throw new Error("The selected file is not valid JSON.");
    }
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
      throw new Error("The selected file must contain a JSON object.");
    }
    return normalizeDocument(raw);
  }

  private async setSelectedPath(dataPath: string): Promise<void> {
    this.selectedPath = resolve(dataPath);
    await this.writeConfig({ dataFile: this.selectedPath });
  }

  private async readConfig(): Promise<LocalConfig> {
    try {
      const content = await readFile(this.configPath, "utf8");
      const parsed: unknown = JSON.parse(content);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return parsed as LocalConfig;
      }
    } catch {
      return {};
    }
    return {};
  }

  private async writeConfig(config: LocalConfig): Promise<void> {
    await writeJsonAtomically(this.configPath, config);
  }
}

import { app, BrowserWindow, ipcMain } from "electron";
import { join, resolve } from "node:path";
import { DataStore } from "./data-store";
import type { FinanceDocument } from "../shared/types";

let mainWindow: BrowserWindow | null = null;
let dataStore: DataStore;

if (process.env.FINANCE_TRACKER_USER_DATA) {
  app.setPath("userData", resolve(process.env.FINANCE_TRACKER_USER_DATA));
}

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 700,
    backgroundColor: "#071b18",
    title: "Finance Tracker Modern",
    webPreferences: {
      preload: join(__dirname, "../preload/index.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  if (process.env.ELECTRON_RENDERER_URL) {
    void mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL);
  } else {
    void mainWindow.loadFile(join(__dirname, "../renderer/index.html"));
  }
}

app.whenReady().then(() => {
  app.setAppUserModelId("com.molze.financetracker");
  const developmentDefault = app.isPackaged
    ? null
    : resolve(app.getAppPath(), "..", "finance_data.json");
  dataStore = new DataStore(
    join(app.getPath("userData"), "finance-tracker-modern.json"),
    developmentDefault
  );

  ipcMain.handle("finance:load", () => dataStore.load());
  ipcMain.handle("finance:chooseDataFile", () => dataStore.chooseDataFile(mainWindow ?? undefined));
  ipcMain.handle("finance:createDataFile", () => dataStore.createDataFile(mainWindow ?? undefined));
  ipcMain.handle("finance:saveDocument", (_event, document: FinanceDocument) => dataStore.saveDocument(document));
  ipcMain.handle("finance:chooseBankCsv", () => dataStore.chooseBankCsv(mainWindow ?? undefined));
  ipcMain.handle("finance:exportText", (_event, defaultName: string, text: string) => {
    return dataStore.exportText(defaultName, text, mainWindow ?? undefined);
  });

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

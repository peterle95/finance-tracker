import { contextBridge, ipcRenderer } from "electron";
import type { FinanceApi, FinanceDocument } from "../shared/types";

const financeApi: FinanceApi = {
  load: () => ipcRenderer.invoke("finance:load"),
  chooseDataFile: () => ipcRenderer.invoke("finance:chooseDataFile"),
  createDataFile: () => ipcRenderer.invoke("finance:createDataFile"),
  saveDocument: (previous: FinanceDocument, document: FinanceDocument) => ipcRenderer.invoke("finance:saveDocument", previous, document),
  chooseBankCsv: () => ipcRenderer.invoke("finance:chooseBankCsv"),
  exportText: (defaultName: string, text: string) => ipcRenderer.invoke("finance:exportText", defaultName, text)
};

contextBridge.exposeInMainWorld("finance", financeApi);

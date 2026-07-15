import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const installer = resolve("node_modules", "electron", "install.js");

if (!existsSync(installer)) {
  process.exit(0);
}

const result = spawnSync(process.execPath, [installer], { stdio: "inherit" });

if (result.error) {
  throw result.error;
}

process.exit(result.status ?? 1);

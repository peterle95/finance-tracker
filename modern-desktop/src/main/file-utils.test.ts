import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { writeJsonAtomically } from "./file-utils";

describe("writeJsonAtomically", () => {
  it("replaces the target with valid formatted JSON", async () => {
    const directory = await mkdtemp(join(tmpdir(), "finance-modern-"));
    const target = join(directory, "finance_data.json");
    try {
      await writeJsonAtomically(target, { expenses: [{ amount: 12.5 }] });
      const saved = await readFile(target, "utf8");
      expect(JSON.parse(saved)).toEqual({ expenses: [{ amount: 12.5 }] });
      expect(saved.endsWith("\n")).toBe(true);
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });
});

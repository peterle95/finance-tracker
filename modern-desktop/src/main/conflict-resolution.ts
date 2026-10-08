import { isDeepStrictEqual } from "node:util";
import type { ConflictDifference, ConflictResolution } from "../shared/types";

const OWNER_FILES = new Set(["categories.json", "budget.json", "net_worth.json", "loans.json", "savings_goals.json", "preferences.json"]);

export function conflictOriginalName(fileName: string): string | null {
  const match = /^(.+)\.sync-conflict-[a-z0-9-]+\.json$/i.exec(fileName);
  if (!match) return null;
  const original = match[1] + ".json";
  return OWNER_FILES.has(original) || /^transactions_(expense|income)_[a-z0-9]+(?:-[a-z0-9]+)*\.json$/.test(original)
    ? original : null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function parse(text: string | null) {
  if (text === null) return { value: undefined, error: "The current file is missing." };
  try {
    return { value: JSON.parse(text) as unknown, error: undefined };
  } catch {
    return { value: undefined, error: "This version is not valid JSON." };
  }
}

function parts(value: unknown, fileName: string): Map<string, unknown> | null {
  if (isRecord(value)) return new Map(Object.entries(value));
  const identity = fileName === "savings_goals.json" ? "name" : "id";
  if (!Array.isArray(value) || !value.every((item) => isRecord(item)
    && typeof item[identity] === "string" && item[identity].trim())) return null;
  const entries = new Map(value.map((item) => [item[identity] as string, item]));
  return entries.size === value.length ? entries : null;
}

function display(value: unknown): string {
  return value === undefined ? "Not present" : JSON.stringify(value, null, 2);
}

export function compareConflict(fileName: string, currentText: string | null, conflictText: string) {
  const current = parse(currentText);
  const conflict = parse(conflictText);
  const currentParts = current.error ? null : parts(current.value, fileName);
  const conflictParts = conflict.error ? null : parts(conflict.value, fileName);
  const canMerge = Boolean(currentParts && conflictParts && Array.isArray(current.value) === Array.isArray(conflict.value));
  const differences: ConflictDifference[] = [];
  if (canMerge) {
    for (const key of new Set([...currentParts!.keys(), ...conflictParts!.keys()])) {
      const left = currentParts!.get(key);
      const right = conflictParts!.get(key);
      if (isDeepStrictEqual(left, right)) continue;
      const row = isRecord(left) ? left : isRecord(right) ? right : {};
      const name = Array.isArray(current.value) ? row.borrower ?? row.name ?? row.description : undefined;
      differences.push({ key, label: name ? `${name} (${key})` : key, currentText: display(left), conflictText: display(right) });
    }
  } else if (current.error || conflict.error || !isDeepStrictEqual(current.value, conflict.value)) {
    differences.push({ key: "file", label: "Entire file", currentText: currentText ?? "File missing", conflictText });
  }
  return { current, conflict, currentParts, conflictParts, canMerge, differences };
}

export function resolveConflictValue(comparison: ReturnType<typeof compareConflict>, resolution: ConflictResolution): unknown {
  if (resolution.source === "current" || resolution.source === "conflict") {
    const version = resolution.source === "current" ? comparison.current : comparison.conflict;
    if (version.error) throw new Error(version.error);
    return version.value;
  }
  if (resolution.source !== "merge" || !comparison.canMerge || !resolution.choices) {
    throw new Error("Choose a valid conflict resolution.");
  }
  for (const difference of comparison.differences) {
    if (!Object.hasOwn(resolution.choices, difference.key)
      || !["current", "conflict"].includes(resolution.choices[difference.key])) {
      throw new Error("Choose a version for every difference before saving.");
    }
  }
  const entries = new Map(comparison.currentParts!);
  for (const difference of comparison.differences) {
    if (resolution.choices[difference.key] !== "conflict") continue;
    if (comparison.conflictParts!.has(difference.key)) entries.set(difference.key, comparison.conflictParts!.get(difference.key));
    else entries.delete(difference.key);
  }
  return Array.isArray(comparison.current.value) ? [...entries.values()] : Object.fromEntries(entries);
}

import { useEffect, useState } from "react";

export interface KeyboardNavigationOptions {
  activationKey?: string;
  alphabet?: string;
  immediate?: boolean;
  hintTimeout?: number;
}

export type KeyboardNavigationSettings = { activationKey: string; hintAlphabet: string; activationMode: "select" | "immediate" };
export const DEFAULT_KEYBOARD_NAVIGATION: KeyboardNavigationSettings = { activationKey: " ", hintAlphabet: "asdfjkl", activationMode: "select" };

export function normalizeKeyboardNavigationSettings(value: unknown): KeyboardNavigationSettings {
  if (!value || typeof value !== "object") return DEFAULT_KEYBOARD_NAVIGATION;
  const candidate = value as Partial<KeyboardNavigationSettings>;
  const activationKey = typeof candidate.activationKey === "string" ? candidate.activationKey.trim().toLowerCase() : "";
  const hintAlphabet = typeof candidate.hintAlphabet === "string"
    ? [...candidate.hintAlphabet.toLowerCase().replace(/\s/g, "")].filter((key, index, keys) => keys.indexOf(key) === index).join("")
    : "";
  if (activationKey.length !== 1 || !hintAlphabet || !/^[a-z]+$/.test(hintAlphabet) || [...hintAlphabet].length < 2 || candidate.activationMode !== "select" && candidate.activationMode !== "immediate") {
    return DEFAULT_KEYBOARD_NAVIGATION;
  }
  return { activationKey, hintAlphabet, activationMode: candidate.activationMode };
}

const regions = ["sidebar", "header", "main", "dialog"] as const;
type Region = (typeof regions)[number];

const actionable = "button, a[href], input, select, textarea, [role=button], [role=tab], [role=menuitem], [tabindex]:not([tabindex='-1'])";

function visible(element: Element): element is HTMLElement {
  const node = element as HTMLElement;
  const style = window.getComputedStyle(node);
  return !node.closest("[hidden], [inert], [aria-hidden='true']") && !node.hasAttribute("disabled") && node.getAttribute("aria-disabled") !== "true" && style.display !== "none" && style.visibility !== "hidden";
}

function editing(element: Element | null) {
  return element !== null && (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement || element.closest("[contenteditable]") !== null);
}

function hintNames(alphabet: string, count: number) {
  const names: string[] = [];
  const queue = [""];
  while (names.length < count) {
    const prefix = queue.shift()!;
    for (const character of alphabet) {
      const name = prefix + character;
      names.push(name);
      queue.push(name);
      if (names.length === count) break;
    }
  }
  return names;
}

export function useKeyboardNavigation({ activationKey = " ", alphabet = "ASDFJKL", immediate = false, hintTimeout = 1000 }: KeyboardNavigationOptions = {}) {
  const [active, setActive] = useState(false);
  const [region, setRegion] = useState<Region>("main");

  useEffect(() => {
    document.documentElement.dataset.keyboardMode = active ? "active" : "off";
    document.documentElement.dataset.keyboardRegion = region;
    return () => {
      delete document.documentElement.dataset.keyboardMode;
      delete document.documentElement.dataset.keyboardRegion;
    };
  }, [active, region]);

  useEffect(() => {
    let buffer = "";
    let timer: number | undefined;
    let selected: HTMLElement | undefined;

    const clear = () => { buffer = ""; selected = undefined; document.querySelectorAll("[data-keyboard-hint]").forEach((node) => node.removeAttribute("data-keyboard-hint")); };
    const topDialog = () => Array.from(document.querySelectorAll<HTMLElement>("[role='dialog']")).filter(visible).at(-1);
    const targets = (area: Region) => {
  const dialog = topDialog();
      if (dialog) {
        return Array.from(dialog.querySelectorAll(actionable)).filter((target) => target.closest("[role='dialog']") === dialog).filter(visible) as HTMLElement[];
      }
      return Array.from(document.querySelectorAll(`[data-keyboard-region='${area}'] ${actionable}`)).filter(visible) as HTMLElement[];
    };
    const showHints = () => {
      clear();
      const names = hintNames(alphabet.toUpperCase(), targets(region).length);
      targets(region).forEach((target, index) => target.setAttribute("data-keyboard-hint", names[index]));
    };
    const activate = (target: HTMLElement) => {
      window.clearTimeout(timer);
      target.click();
      clear();
      window.setTimeout(showHints, 0);
    };
    const stop = () => { clear(); setActive(false); };
    const onKey = (event: KeyboardEvent) => {
      if (!document.hasFocus()) return;
      if (event.key === "Escape" && active && !topDialog()) { event.preventDefault(); stop(); return; }
      if (editing(document.activeElement)) return;
       if (event.key === " " || event.key.toLowerCase() === activationKey) {
         event.preventDefault();
         if (active) { stop(); } else { setActive(true); document.documentElement.dataset.keyboardEntry = "true"; window.setTimeout(() => delete document.documentElement.dataset.keyboardEntry, 500); showHints(); }
         return;
       }
      if (!active) return;
      if ((event.key === "h" || event.key === "l") && !topDialog()) {
        event.preventDefault();
        const step = event.key === "h" ? -1 : 1;
        setRegion((current) => regions[(regions.indexOf(current) + step + regions.length) % regions.length]);
        clear();
        window.setTimeout(showHints, 0);
        return;
      }
      if (event.key === "j" || event.key === "k") {
        event.preventDefault();
        const scrollable = document.querySelector(".page-scroll, .main-panel");
        if (scrollable instanceof HTMLElement && typeof scrollable.scrollBy === "function") {
          scrollable.scrollBy({ top: event.key === "j" ? 360 : -360, behavior: "smooth" });
        }
        return;
      }
      if (event.key === "Backspace") { event.preventDefault(); buffer = buffer.slice(0, -1); showHints(); return; }
      if (event.key === "Enter" && selected) { event.preventDefault(); activate(selected); return; }
      const character = event.key.toUpperCase();
      if (!alphabet.toUpperCase().includes(character)) return;
      event.preventDefault();
      buffer += character;
      const matches = targets(region).filter((target) => target.getAttribute("data-keyboard-hint")?.startsWith(buffer));
      if (matches.length === 1 && matches[0].getAttribute("data-keyboard-hint") === buffer) {
        selected = matches[0];
        selected.focus({ preventScroll: true });
        if (immediate) { activate(selected); return; }
      } else if (!matches.length) clear();
      window.clearTimeout(timer);
      timer = window.setTimeout(clear, hintTimeout);
    };
    document.addEventListener("keydown", onKey);
    const observer = new MutationObserver(() => {
      if (active) showHints();
      else clear();
    });
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["aria-hidden", "hidden", "style"] });
    return () => { document.removeEventListener("keydown", onKey); observer.disconnect(); window.clearTimeout(timer); };
  }, [activationKey, active, alphabet, immediate, hintTimeout, region]);

  return { active, region };
}

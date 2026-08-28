import { useEffect, useState } from "react";

export interface KeyboardNavigationOptions {
  alphabet?: string;
  immediate?: boolean;
  hintTimeout?: number;
}

const regions = ["sidebar", "header", "main", "dialog"] as const;
type Region = (typeof regions)[number];

const actionable = "button, a[href], input, select, textarea, [role=button], [tabindex]:not([tabindex='-1'])";

function visible(element: Element): element is HTMLElement {
  const node = element as HTMLElement;
  const style = window.getComputedStyle(node);
  return !node.closest("[hidden], [inert], [aria-hidden='true']") && !node.hasAttribute("disabled") && node.getAttribute("aria-disabled") !== "true" && style.display !== "none" && style.visibility !== "hidden";
}

function editing(element: Element | null) {
  return element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement || element?.hasAttribute("contenteditable");
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

export function useKeyboardNavigation({ alphabet = "ASDFJKL", immediate = false, hintTimeout = 1000 }: KeyboardNavigationOptions = {}) {
  const [active, setActive] = useState(false);
  const [region, setRegion] = useState<Region>("main");

  useEffect(() => {
    let buffer = "";
    let timer: number | undefined;
    let selected: HTMLElement | undefined;

    const clear = () => { buffer = ""; selected = undefined; document.querySelectorAll("[data-keyboard-hint]").forEach((node) => node.removeAttribute("data-keyboard-hint")); };
    const targets = (area: Region) => {
      if (area === "dialog") {
        const dialogs = Array.from(document.querySelectorAll<HTMLElement>("[role='dialog']")).filter(visible);
        const dialog = dialogs.at(-1);
        return dialog ? Array.from(dialog.querySelectorAll(actionable)).filter(visible) as HTMLElement[] : [];
      }
      if (document.querySelector("[role='dialog']")) return [];
      return Array.from(document.querySelectorAll(`[data-keyboard-region='${area}'] ${actionable}`)).filter(visible) as HTMLElement[];
    };
    const showHints = () => {
      clear();
      const names = hintNames(alphabet.toUpperCase(), targets(region).length);
      targets(region).forEach((target, index) => target.setAttribute("data-keyboard-hint", names[index]));
    };
    const stop = () => { clear(); setActive(false); };
    const onKey = (event: KeyboardEvent) => {
      if (!document.hasFocus()) return;
      if (event.key === "Escape" && active) { event.preventDefault(); stop(); return; }
      if (editing(document.activeElement)) return;
      if (!active && event.key === " ") { event.preventDefault(); setActive(true); showHints(); return; }
      if (!active) return;
      if (event.key === "h" || event.key === "l") {
        event.preventDefault();
        const step = event.key === "h" ? -1 : 1;
        setRegion((current) => regions[(regions.indexOf(current) + step + regions.length) % regions.length]);
        clear();
        window.setTimeout(showHints, 0);
        return;
      }
      if (event.key === "j" || event.key === "k") {
        event.preventDefault();
        document.querySelector(".page-scroll, .main-panel")?.scrollBy({ top: event.key === "j" ? 360 : -360, behavior: "smooth" });
        return;
      }
      if (event.key === "Backspace") { event.preventDefault(); buffer = buffer.slice(0, -1); showHints(); return; }
      if (event.key === "Enter" && selected) { event.preventDefault(); selected.click(); clear(); return; }
      const character = event.key.toUpperCase();
      if (!alphabet.toUpperCase().includes(character)) return;
      event.preventDefault();
      buffer += character;
      const matches = targets(region).filter((target) => target.getAttribute("data-keyboard-hint")?.startsWith(buffer));
      if (matches.length === 1 && matches[0].getAttribute("data-keyboard-hint") === buffer) {
        selected = matches[0];
        if (immediate) { selected.click(); clear(); }
      } else if (!matches.length) clear();
      window.clearTimeout(timer);
      timer = window.setTimeout(clear, hintTimeout);
    };
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("keydown", onKey); window.clearTimeout(timer); };
  }, [active, alphabet, immediate, hintTimeout, region]);

  return { active, region };
}

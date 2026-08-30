import { useEffect, useRef, useState } from "react";

export interface KeyboardNavigationOptions {
  activationKey?: string;
  alphabet?: string;
  hintTimeout?: number;
}

export type KeyboardNavigationSettings = { activationKey: string; hintAlphabet: string };
export const DEFAULT_KEYBOARD_NAVIGATION: KeyboardNavigationSettings = { activationKey: " ", hintAlphabet: "asdfjkl" };

export function normalizeKeyboardNavigationSettings(value: unknown): KeyboardNavigationSettings {
  if (!value || typeof value !== "object") return DEFAULT_KEYBOARD_NAVIGATION;
  const candidate = value as Partial<KeyboardNavigationSettings>;
  const activationKey = candidate.activationKey === " " ? " " : typeof candidate.activationKey === "string" ? candidate.activationKey.trim().toLowerCase() : "";
  const hintAlphabet = typeof candidate.hintAlphabet === "string"
    ? [...candidate.hintAlphabet.toLowerCase().replace(/\s/g, "")].filter((key, index, keys) => keys.indexOf(key) === index).join("")
    : "";
  if (activationKey.length !== 1 || !hintAlphabet || !/^[a-z0-9]+$/.test(hintAlphabet) || [...hintAlphabet].length < 2) {
    return DEFAULT_KEYBOARD_NAVIGATION;
  }
  return { activationKey, hintAlphabet };
}

const actionable = "button, a[href], input, select, textarea, [role=button], [role=tab], [role=menuitem], [tabindex]:not([tabindex='-1'])";

function visible(element: Element): element is HTMLElement {
  const node = element as HTMLElement;
  if (!node.isConnected || node.matches(":disabled") || node.closest("[hidden], [inert], [aria-hidden='true'], [aria-disabled='true']")) return false;
  for (let ancestor: HTMLElement | null = node; ancestor; ancestor = ancestor.parentElement) {
    const style = window.getComputedStyle(ancestor);
    if (style.display === "none" || style.visibility === "hidden" || style.visibility === "collapse") return false;
  }
  return true;
}

function editing(element: Element | null) {
  return element !== null && (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement || element.closest("[contenteditable]") !== null);
}

function hintNames(alphabet: string, count: number) {
  let length = 1;
  while (alphabet.length ** length < count) {
    length += 1;
  }
  return Array.from({ length: count }, (_, index) => {
    let value = index;
    let name = "";
    for (let position = 0; position < length; position += 1) {
      name = alphabet[value % alphabet.length] + name;
      value = Math.floor(value / alphabet.length);
    }
    return name;
  });
}

export function useKeyboardNavigation({ activationKey = " ", alphabet = "ASDFJKL", hintTimeout = 1000 }: KeyboardNavigationOptions = {}) {
  const [active, setActive] = useState(false);
  const activeRef = useRef(false);

  useEffect(() => {
    document.documentElement.dataset.keyboardMode = active ? "active" : "off";
    return () => {
      delete document.documentElement.dataset.keyboardMode;
    };
  }, [active]);

  useEffect(() => {
    let buffer = "";
    let timer: number | undefined;
    let entryTimer: number | undefined;
    let hints: Array<{ target: HTMLElement; name: string }> = [];

    const clearTimer = () => {
      window.clearTimeout(timer);
      timer = undefined;
    };
    const clearHints = () => {
      hints = [];
      document.querySelectorAll("[data-keyboard-hint]").forEach((node) => node.removeAttribute("data-keyboard-hint"));
    };
    const topDialog = () => Array.from(document.querySelectorAll<HTMLElement>("[role='dialog']")).filter(visible).at(-1);
    const targets = () => {
      const dialog = topDialog();
      if (dialog) {
        return Array.from(dialog.querySelectorAll(actionable)).filter((target) => target.closest("[role='dialog']") === dialog).filter(visible) as HTMLElement[];
      }
      return Array.from(document.querySelectorAll(actionable)).filter(visible) as HTMLElement[];
    };
    const showHints = () => {
      clearHints();
      const currentTargets = targets();
      const names = hintNames(alphabet.toUpperCase(), currentTargets.length);
      hints = currentTargets.map((target, index) => ({ target, name: names[index] }));
      hints.forEach(({ target, name }) => target.setAttribute("data-keyboard-hint", name));
    };
    const activate = (target: HTMLElement) => {
      clearTimer();
      target.focus({ preventScroll: true });
      target.click();
      buffer = "";
      clearHints();
      window.setTimeout(() => { if (activeRef.current) showHints(); }, 0);
    };
    const stop = () => {
      clearTimer();
      buffer = "";
      clearHints();
      activeRef.current = false;
      setActive(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (!document.hasFocus() || event.isComposing || event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
      if (event.key === "Escape") {
        if (activeRef.current && !topDialog()) { event.preventDefault(); stop(); }
        return;
      }
      if (editing(document.activeElement)) return;
      const character = event.key.toUpperCase();
      const isHintCharacter = alphabet.toUpperCase().includes(character);
      const isActivationKey = event.key.toLowerCase() === activationKey;
      if (!activeRef.current) {
        if (!isActivationKey || event.repeat) return;
        event.preventDefault();
        activeRef.current = true;
        setActive(true);
        document.documentElement.dataset.keyboardEntry = "true";
        entryTimer = window.setTimeout(() => delete document.documentElement.dataset.keyboardEntry, 500);
        showHints();
        return;
      }
      if (isActivationKey && !isHintCharacter) { event.preventDefault(); stop(); return; }
      if (event.key === "Backspace") { event.preventDefault(); buffer = buffer.slice(0, -1); showHints(); return; }
      if (event.key === "Enter") { event.preventDefault(); return; }
      if (!isHintCharacter) return;
      event.preventDefault();
      buffer += character;
      const matches = hints.filter(({ target, name }) => target.isConnected && name.startsWith(buffer));
      if (matches.length === 1 && matches[0].name === buffer) {
        activate(matches[0].target);
        return;
      }
      if (!matches.length) {
        buffer = "";
        showHints();
        return;
      }
      clearTimer();
      timer = window.setTimeout(() => {
        buffer = "";
        if (activeRef.current) showHints();
      }, hintTimeout);
    };
    document.addEventListener("keydown", onKey);
    const observer = new MutationObserver(() => {
      if (activeRef.current) showHints();
    });
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["aria-hidden", "hidden", "inert", "style", "class", "disabled", "aria-disabled", "tabindex"] });
    if (activeRef.current) showHints();
    return () => {
      document.removeEventListener("keydown", onKey);
      observer.disconnect();
      clearTimer();
      window.clearTimeout(entryTimer);
      clearHints();
      delete document.documentElement.dataset.keyboardEntry;
    };
  }, [activationKey, alphabet, hintTimeout]);

  return { active };
}

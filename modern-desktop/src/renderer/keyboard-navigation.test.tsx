import { cleanup, render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { normalizeKeyboardNavigationSettings, useKeyboardNavigation } from "./keyboard-navigation";

function Fixture({ mainCount = 2, onClick = vi.fn(), onSideClick = vi.fn() }: { mainCount?: number; onClick?: (index: number) => void; onSideClick?: () => void }) {
  useKeyboardNavigation({ hintTimeout: 20 });
  return <><nav data-keyboard-region="sidebar"><button onClick={onSideClick}>Side</button></nav><main data-keyboard-region="main">{Array.from({ length: mainCount }, (_, index) => <button key={index} onClick={() => onClick(index)}>Item {index + 1}</button>)}</main></>;
}

function CustomActivationFixture() {
  useKeyboardNavigation({ activationKey: "g" });
  return <button>Action</button>;
}

describe("keyboard navigation", () => {
  afterEach(cleanup);

  it("accepts numeric hint alphabet settings", () => {
    expect(normalizeKeyboardNavigationSettings({ activationKey: " ", hintAlphabet: "123" })).toEqual({ activationKey: " ", hintAlphabet: "123" });
  });

  it("keeps mode active and redraws hints after immediate activation", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const user = userEvent.setup();
    render(<Fixture />);
    await user.keyboard(" ");
    expect(document.documentElement.dataset.keyboardMode).toBe("active");
    expect(document.querySelector("button[data-keyboard-hint='A']")).toBeTruthy();
    await user.keyboard("a");
    await new Promise((resolve) => window.setTimeout(resolve));
    expect(document.documentElement.dataset.keyboardMode).toBe("active");
    expect(document.querySelector("button[data-keyboard-hint='A']")).toBeTruthy();
  });

  it("shows hints for every visible action", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const user = userEvent.setup();
    render(<Fixture />);

    await user.keyboard(" ");
    expect(Array.from(document.querySelectorAll("button"), (button) => button.getAttribute("data-keyboard-hint"))).toEqual(["A", "S", "D"]);
  });

  it("ignores actions hidden by a parent", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const user = userEvent.setup();
    render(<><Fixture /><div style={{ display: "none" }}><button>Hidden</button></div></>);

    await user.keyboard(" ");
    expect(document.querySelector("button")?.getAttribute("data-keyboard-hint")).toBe("A");
    expect(Array.from(document.querySelectorAll("button"), (button) => button.getAttribute("data-keyboard-hint"))).toEqual(["A", "S", "D", null]);
  });

  it("uses prefix-free hints when there are more actions than alphabet keys", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const onSideClick = vi.fn();
    const user = userEvent.setup();
    render(<Fixture mainCount={7} onSideClick={onSideClick} />);

    await user.keyboard(" ");
    expect(Array.from(document.querySelectorAll("button"), (button) => button.getAttribute("data-keyboard-hint"))).toEqual(["AA", "AS", "AD", "AF", "AJ", "AK", "AL", "SA"]);
    await user.keyboard("aa");
    expect(onSideClick).toHaveBeenCalledOnce();
  });

  it("activates a J hint immediately", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<Fixture mainCount={5} onClick={onClick} />);

    await user.keyboard(" ");
    await user.keyboard("j");
    expect(onClick).toHaveBeenCalledWith(3);
  });

  it("activates a multi-character hint immediately", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<Fixture mainCount={12} onClick={onClick} />);

    await user.keyboard(" ");
    await user.keyboard("sk");
    expect(onClick).toHaveBeenCalledWith(11);
  });

  it("recovers from an invalid hint sequence", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const onSideClick = vi.fn();
    const user = userEvent.setup();
    render(<Fixture mainCount={7} onSideClick={onSideClick} />);

    await user.keyboard(" ");
    await user.keyboard("l");
    await user.keyboard("aa");
    expect(onSideClick).toHaveBeenCalledOnce();
  });

  it("restores hints after a partial sequence times out", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const user = userEvent.setup();
    render(<Fixture mainCount={7} />);

    await user.keyboard(" ");
    await user.keyboard("a");
    await new Promise((resolve) => window.setTimeout(resolve, 30));
    expect(document.querySelector("button")?.getAttribute("data-keyboard-hint")).toBe("AA");
  });

  it("does not capture modified keyboard shortcuts", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const onSideClick = vi.fn();
    const user = userEvent.setup();
    render(<Fixture onSideClick={onSideClick} />);

    await user.keyboard(" ");
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "a", ctrlKey: true, bubbles: true, cancelable: true }));
    expect(onSideClick).not.toHaveBeenCalled();
  });

  it("uses the configured activation key instead of Space", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const user = userEvent.setup();
    render(<CustomActivationFixture />);

    await user.keyboard(" ");
    expect(document.documentElement.dataset.keyboardMode).toBe("off");
    await user.keyboard("g");
    expect(document.documentElement.dataset.keyboardMode).toBe("active");
  });

  it("does not consume typing in an editor", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const user = userEvent.setup();
    render(<><Fixture /><input /></>);
    const input = document.querySelector("input")!;
    await user.click(input);
    await user.keyboard(" ");
    expect(input.value).toBe(" ");
  });

  it("routes hints to the topmost dialog and restores background navigation", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const user = userEvent.setup();
    const { rerender } = render(<><Fixture /><div role="dialog"><button>Outer</button><div role="dialog"><button>Inner</button></div></div></>);
    await user.keyboard(" ");
    expect(document.querySelector("button[data-keyboard-hint='A']")?.textContent).toBe("Inner");
    rerender(<Fixture />);
    await user.keyboard("a");
    expect(document.querySelector("button[data-keyboard-hint='A']")?.textContent).toBe("Side");
  });

  it("preserves Enter and Space in contenteditable", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const user = userEvent.setup();
    render(<><Fixture /><div contentEditable><span>edit</span></div></>);
    const editor = document.querySelector("[contenteditable]")!;
    await user.click(editor);
    const space = new KeyboardEvent("keydown", { key: " ", bubbles: true });
    const enter = new KeyboardEvent("keydown", { key: "Enter", bubbles: true });
    editor.dispatchEvent(space);
    editor.dispatchEvent(enter);
    expect(space.defaultPrevented).toBe(false);
    expect(enter.defaultPrevented).toBe(false);
  });
});

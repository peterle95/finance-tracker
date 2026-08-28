import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { useKeyboardNavigation } from "./keyboard-navigation";

function Fixture() {
  useKeyboardNavigation({ hintTimeout: 20 });
  return <><nav data-keyboard-region="sidebar"><button onClick={vi.fn()}>Side</button></nav><main data-keyboard-region="main"><button>One</button><button>Two</button></main></>;
}

describe("keyboard navigation", () => {
  it("keeps mode active and redraws hints after selecting with Enter", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const user = userEvent.setup();
    render(<Fixture />);
    await user.keyboard(" ");
    expect(document.documentElement.dataset.keyboardMode).toBe("active");
    expect(document.querySelector("button[data-keyboard-hint='A']")).toBeTruthy();
    await user.keyboard("a{Enter}");
    await new Promise((resolve) => window.setTimeout(resolve));
    expect(document.documentElement.dataset.keyboardMode).toBe("active");
    expect(document.querySelector("button[data-keyboard-hint='A']")).toBeTruthy();
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
    await user.keyboard("a{Enter}");
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

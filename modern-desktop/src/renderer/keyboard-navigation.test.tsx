import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { useKeyboardNavigation } from "./keyboard-navigation";

function Fixture() {
  useKeyboardNavigation({ hintTimeout: 20 });
  return <><nav data-keyboard-region="sidebar"><button onClick={vi.fn()}>Side</button></nav><main data-keyboard-region="main"><button>One</button><button>Two</button></main></>;
}

describe("keyboard navigation", () => {
  it("enters with Space and selects a hint with Enter", async () => {
    vi.spyOn(document, "hasFocus").mockReturnValue(true);
    const user = userEvent.setup();
    render(<Fixture />);
    await user.keyboard(" ");
    expect(document.querySelector("button[data-keyboard-hint='A']")).toBeTruthy();
    await user.keyboard("a{Enter}");
    expect(document.querySelector("button[data-keyboard-hint='A']")).toBeNull();
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
});

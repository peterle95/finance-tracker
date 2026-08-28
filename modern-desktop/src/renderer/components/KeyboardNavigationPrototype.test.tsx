import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { KeyboardNavigationPrototype } from "./KeyboardNavigationPrototype";

describe("KeyboardNavigationPrototype", () => {
  it("enters mode and dismisses help", async () => {
    const user = userEvent.setup();
    render(<KeyboardNavigationPrototype reducedMotion={false} />);

    await user.click(screen.getByRole("button", { name: "Enter keyboard mode" }));
    expect(screen.getByRole("status").textContent).toBe("Keyboard mode on");
    expect(screen.getByRole("button", { name: "Overview" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Dismiss keyboard help" }));
    expect(screen.queryByRole("complementary")).toBeNull();
  });
});

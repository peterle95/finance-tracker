import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DEFAULT_BEHAVIOR_SETTINGS } from "../../shared/behavior-settings";
import { DEFAULT_RANGE_SETTINGS } from "../../shared/range-settings";
import { defaultDocument } from "../../shared/finance";
import { SettingsScreen } from "./SettingsScreen";

describe("SettingsScreen keyboard navigation prototype", () => {
  it("validates and resets local keyboard settings", async () => {
    const user = userEvent.setup();
    render(<SettingsScreen document={defaultDocument()} connection={{ path: null, isConnected: false }} theme="dark" reducedMotion={false}
      defaultRanges={DEFAULT_RANGE_SETTINGS} defaultBehaviors={DEFAULT_BEHAVIOR_SETTINGS} onThemeChange={vi.fn()} onReducedMotionChange={vi.fn()}
      onDefaultRangesChange={vi.fn()} onDefaultBehaviorsChange={vi.fn()} onDefaultNetWorthPeriodChange={vi.fn()} onDefaultNetWorthBreakdownPeriodChange={vi.fn()}
      onChooseFile={vi.fn()} onCreateFile={vi.fn()} onReload={vi.fn()} />);

    await user.clear(screen.getByLabelText("Activation key"));
    expect(screen.getByText("Use one non-space key.")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Activate immediately" }));
    await user.click(screen.getByRole("button", { name: "Reset keyboard defaults" }));

    expect((screen.getByLabelText("Activation key") as HTMLInputElement).value).toBe("f");
    expect(screen.getByRole("button", { name: "Select, then Enter" }).className).toContain("selected");
  });
});

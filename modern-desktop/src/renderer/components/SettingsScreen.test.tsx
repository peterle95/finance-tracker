import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DEFAULT_BEHAVIOR_SETTINGS } from "../../shared/behavior-settings";
import { DEFAULT_RANGE_SETTINGS } from "../../shared/range-settings";
import { defaultDocument } from "../../shared/finance";
import { SettingsScreen } from "./SettingsScreen";
import { DEFAULT_KEYBOARD_NAVIGATION } from "../keyboard-navigation";

describe("SettingsScreen keyboard navigation prototype", () => {
  it("validates and resets local keyboard settings", async () => {
    const user = userEvent.setup();
    const onKeyboardNavigationChange = vi.fn();
    const onKeyboardNavigationReset = vi.fn();
    render(<SettingsScreen document={defaultDocument()} connection={{ path: null, isConnected: false }} theme="dark" reducedMotion={false}
      defaultRanges={DEFAULT_RANGE_SETTINGS} defaultBehaviors={DEFAULT_BEHAVIOR_SETTINGS} onThemeChange={vi.fn()} onReducedMotionChange={vi.fn()}
      onDefaultRangesChange={vi.fn()} onDefaultBehaviorsChange={vi.fn()} onDefaultNetWorthPeriodChange={vi.fn()} onDefaultNetWorthBreakdownPeriodChange={vi.fn()}
      onChooseFile={vi.fn()} onCreateFile={vi.fn()} onReload={vi.fn()} keyboardNavigation={DEFAULT_KEYBOARD_NAVIGATION}
      onKeyboardNavigationChange={onKeyboardNavigationChange} onKeyboardNavigationReset={onKeyboardNavigationReset} />);

    await user.clear(screen.getByLabelText("Activation key"));
    expect(onKeyboardNavigationChange).toHaveBeenCalledWith(expect.objectContaining({ activationKey: "" }));
    await user.click(screen.getByRole("button", { name: "Activate immediately" }));
    await user.click(screen.getByRole("button", { name: "Reset keyboard defaults" }));

    expect((screen.getByLabelText("Activation key") as HTMLInputElement).value).toBe(" ");
    expect(onKeyboardNavigationReset).toHaveBeenCalled();
  });
});

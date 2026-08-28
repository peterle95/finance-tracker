import { useState } from "react";
import { Button } from "./ui";

interface KeyboardNavigationPrototypeProps {
  reducedMotion: boolean;
}

export function KeyboardNavigationPrototype({ reducedMotion }: KeyboardNavigationPrototypeProps) {
  const [active, setActive] = useState(false);
  const [helpOpen, setHelpOpen] = useState(true);
  const [regionChanged, setRegionChanged] = useState(false);

  function enterMode() {
    setActive(true);
    setRegionChanged(false);
  }

  return (
    <div className={"keyboard-prototype " + (active ? "keyboard-prototype-active " : "") + (regionChanged ? "keyboard-prototype-region-changed" : "")}>
      <div className="keyboard-prototype-heading">
        <div><p className="eyebrow">Visual feedback demo</p><h3>Try keyboard mode</h3></div>
        <span className="keyboard-mode-indicator" role="status">{active ? "Keyboard mode on" : "Keyboard mode off"}</span>
      </div>
      <p className="muted-copy">Prototype only: press the control, then Tab through targets to preview the feedback.</p>
      <div className="keyboard-prototype-actions">
        <Button onClick={enterMode}>{active ? "Replay mode entry" : "Enter keyboard mode"}</Button>
        <Button variant="ghost" onClick={() => setHelpOpen(true)}>Show keyboard help</Button>
      </div>
      {active ? (
        <div className="keyboard-prototype-targets" aria-label="Keyboard navigation demo targets">
          <button type="button" onFocus={() => setRegionChanged(false)}>Overview</button>
          <button type="button" onFocus={() => setRegionChanged(true)}>Transactions</button>
          <button type="button" onFocus={() => setRegionChanged(false)}>Settings</button>
        </div>
      ) : null}
      {helpOpen ? (
        <aside className="keyboard-help" aria-label="Keyboard navigation help">
          <button type="button" className="icon-button keyboard-help-dismiss" onClick={() => setHelpOpen(false)} aria-label="Dismiss keyboard help">×</button>
          <strong>Keyboard mode</strong>
          <span>Tab moves focus. Gold glow marks the focused target; a brighter pulse marks a region change.</span>
        </aside>
      ) : null}
      {reducedMotion ? <small className="muted-copy keyboard-motion-note">Reduced motion: static feedback shown.</small> : null}
    </div>
  );
}

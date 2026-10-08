import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import type { ConflictPreview, ConflictResolution, DataConflict, DataLoadResult } from "../../shared/types";
import { Button } from "./ui";

interface ConflictResolverProps {
  fileName: string;
  conflicts: DataConflict[];
  onClose(): void;
  onResolved(result: DataLoadResult): void;
}

function fullPath(directory: string, fileName: string): string {
  return directory.replace(/[\\/]$/, "") + (directory.includes("\\") ? "\\" : "/") + fileName;
}

export function ConflictResolver({ fileName, conflicts, onClose, onResolved }: ConflictResolverProps) {
  const [selectedFile, setSelectedFile] = useState(fileName);
  const [preview, setPreview] = useState<ConflictPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [pending, setPending] = useState<ConflictResolution | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setPreview(null);
    setPending(null);
    setError("");
    window.finance.readConflict(selectedFile).then((result) => {
      if (!cancelled) setPreview(result);
    }).catch((failure: unknown) => {
      if (!cancelled) setError(failure instanceof Error ? failure.message : "The conflict could not be read.");
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [selectedFile, refresh]);

  async function resolve() {
    if (!preview || !pending || busy) return;
    setBusy(true);
    setError("");
    try {
      onResolved(await window.finance.resolveConflict(preview, pending));
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Resolution failed. The conflict copy was kept.");
      setPending(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog.Root open onOpenChange={(open) => { if (!open && !busy) onClose(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay conflict-overlay" />
        <Dialog.Content className="dialog-content conflict-dialog">
          <div className="dialog-heading">
            <div>
              <p className="eyebrow">Desktop conflict resolution</p>
              <Dialog.Title>Resolve sync conflict</Dialog.Title>
              <Dialog.Description>Compare the versions, choose what to keep, then confirm removal of the conflict copy.</Dialog.Description>
            </div>
            <Dialog.Close asChild><button className="icon-button" disabled={busy} aria-label="Close conflict resolver"><X size={18} /></button></Dialog.Close>
          </div>
          <div className="conflict-toolbar">
            <label><span>Conflict file</span><select value={selectedFile} disabled={busy} onChange={(event) => setSelectedFile(event.target.value)}>
              {conflicts.map((conflict) => <option key={conflict.fileName} value={conflict.fileName}>{conflict.fileName}</option>)}
            </select></label>
            <Button variant="secondary" disabled={busy || loading} onClick={() => setRefresh((value) => value + 1)}>Refresh preview</Button>
          </div>
          {loading ? <p role="status">Loading conflict versions…</p> : null}
          {error ? <p className="error-copy" role="alert">{error}</p> : null}
          {preview ? <>
            <div className="conflict-paths">
              <p>Current file: <code>{fullPath(preview.directory, preview.originalFileName)}</code></p>
              <p>Conflict copy: <code>{fullPath(preview.directory, preview.fileName)}</code></p>
            </div>
            {preview.currentError ? <p className="error-copy">Current file: {preview.currentError}</p> : null}
            {preview.conflictError ? <p className="error-copy">Conflict copy: {preview.conflictError}</p> : null}
            {preview.differences.length ? <>
              <p>Only differing records or settings are shown. Choose one complete version.</p>
              <div className="conflict-table-scroll">
                <table className="conflict-comparison">
                  <thead><tr><th>Record / setting</th><th>Current version</th><th>Conflict copy</th></tr></thead>
                  <tbody>{preview.differences.map((difference) => <tr key={difference.key}>
                    <th scope="row">{difference.label}</th>
                    <td><pre tabIndex={0} aria-label={`Current ${difference.label}`}>{difference.currentText}</pre></td>
                    <td><pre tabIndex={0} aria-label={`Conflict ${difference.label}`}>{difference.conflictText}</pre></td>
                  </tr>)}</tbody>
                </table>
              </div>
            </> : <p>The versions contain the same records and settings. Keep the current file to remove the duplicate.</p>}
            <div className="dialog-actions">
              <Button variant="secondary" disabled={busy || Boolean(preview.currentError)} onClick={() => setPending({ source: "current" })}>Keep current file</Button>
              <Button variant="secondary" disabled={busy || Boolean(preview.conflictError)} onClick={() => setPending({ source: "conflict" })}>Use conflict copy</Button>
            </div>
            {pending ? <section className="conflict-confirmation" aria-label="Confirm conflict resolution">
              <h3>Confirm resolution</h3>
              <p>{pending.source === "current" ? "Keep the current content in" : "Replace the current content with the conflict version in"} <code>{preview.originalFileName}</code>.</p>
              <p>Then delete this conflict copy: <code>{fullPath(preview.directory, preview.fileName)}</code>.</p>
              <p>The current filename stays in place for synchronization. This cannot be undone in the app.</p>
              <div className="dialog-actions">
                <Button variant="ghost" disabled={busy} onClick={() => setPending(null)}>Back to review</Button>
                <Button variant="danger" loading={busy} onClick={() => void resolve()}>Confirm resolution</Button>
              </div>
            </section> : null}
          </> : null}
          <div className="dialog-actions"><Dialog.Close asChild><Button variant="ghost" disabled={busy}>Cancel</Button></Dialog.Close></div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

import { useState } from "react";
import { useConfigStore } from "@/stores/configStore";
import { detectRuntime, checkRuntimeDeps } from "@/lib/tauri/commands";
import type { DepCheckResult } from "@/lib/tauri/commands";

export function SettingsPage() {
  const runtime = useConfigStore((s) => s.runtime);
  const runtimeChecked = useConfigStore((s) => s.runtimeChecked);
  const setRuntimeInfo = useConfigStore((s) => s.setRuntimeInfo);
  const rPathOverride = useConfigStore((s) => s.rPathOverride);
  const pixiPathOverride = useConfigStore((s) => s.pixiPathOverride);
  const setRPathOverride = useConfigStore((s) => s.setRPathOverride);
  const setPixiPathOverride = useConfigStore((s) => s.setPixiPathOverride);

  const [deps, setDeps] = useState<DepCheckResult[] | null>(null);
  const [depsLoading, setDepsLoading] = useState(false);

  const handleDetect = async () => {
    try {
      const info = await detectRuntime();
      setRuntimeInfo(info);
    } catch (e) {
      console.error("Runtime detection failed:", e);
    }
  };

  const handleCheckDeps = async () => {
    setDepsLoading(true);
    try {
      const results = await checkRuntimeDeps();
      setDeps(results);
    } catch (e) {
      console.error("Dependency check failed:", e);
    } finally {
      setDepsLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      <h2 className="text-lg font-semibold">Settings</h2>

      <section className="border border-border rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-medium">R Runtime</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Rscript Path:</span>
            <span className="font-mono text-xs">
              {runtime.rPath ?? (
                <span className="text-destructive">Not detected</span>
              )}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">pixi Path:</span>
            <span className="font-mono text-xs">
              {runtime.pixiPath ?? "Not detected"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">R Version:</span>
            <span className="font-mono text-xs">
              {runtime.rVersion ?? "Unknown"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleDetect}
            className="px-3 py-1.5 text-xs bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
          >
            Re-detect Runtime
          </button>
          {runtimeChecked && runtime.rPath && (
            <span className="text-xs text-green-600">R runtime available</span>
          )}
          {runtimeChecked && !runtime.rPath && (
            <span className="text-xs text-destructive">
              R not found — please install R or configure PATH
            </span>
          )}
        </div>
      </section>

      <section className="border border-border rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-medium">Path Overrides</h3>
        <p className="text-xs text-muted-foreground">
          Manually specify paths if auto-detection fails.
        </p>
        <div className="space-y-3">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">
              Rscript Path Override
            </label>
            <input
              type="text"
              value={rPathOverride}
              onChange={(e) => setRPathOverride(e.target.value)}
              placeholder="/usr/bin/Rscript or leave empty for auto-detect"
              className="w-full px-3 py-1.5 text-xs font-mono bg-muted/30 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">
              pixi Path Override
            </label>
            <input
              type="text"
              value={pixiPathOverride}
              onChange={(e) => setPixiPathOverride(e.target.value)}
              placeholder="/usr/local/bin/pixi or leave empty for auto-detect"
              className="w-full px-3 py-1.5 text-xs font-mono bg-muted/30 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>
      </section>

      <section className="border border-border rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium">R Package Dependencies</h3>
          <button
            onClick={handleCheckDeps}
            disabled={depsLoading}
            className="px-3 py-1.5 text-xs bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors disabled:opacity-50"
          >
            {depsLoading ? "Checking..." : "Check Dependencies"}
          </button>
        </div>
        {deps && (
          <div className="grid grid-cols-3 gap-2">
            {deps.map((dep) => (
              <div
                key={dep.package}
                className="flex items-center gap-2 text-xs"
              >
                <span
                  className={
                    dep.installed
                      ? "text-green-600"
                      : "text-destructive"
                  }
                >
                  {dep.installed ? "\u2713" : "\u2717"}
                </span>
                <span className="font-mono">{dep.package}</span>
              </div>
            ))}
          </div>
        )}
        {!deps && (
          <p className="text-xs text-muted-foreground">
            Click &quot;Check Dependencies&quot; to verify required R packages.
          </p>
        )}
      </section>

      <section className="border border-border rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-medium">About</h3>
        <div className="text-sm text-muted-foreground space-y-1">
          <p>Prognosis Marker v0.1.0</p>
          <p>Gene Signature Discovery Platform</p>
          <p>Cross-platform desktop application powered by Tauri</p>
        </div>
      </section>
    </div>
  );
}

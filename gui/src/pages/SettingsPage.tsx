import { useState } from "react";
import { useConfigStore } from "@/stores/configStore";
import { detectRuntime, checkRuntimeDeps, checkEnv, pullDockerImage, installEnv } from "@/lib/tauri/commands";
import type { DepCheckResult } from "@/lib/tauri/commands";
import type { ExecutionBackend } from "@/types/analysis";

export function SettingsPage() {
  const runtime = useConfigStore((s) => s.runtime);
  const runtimeChecked = useConfigStore((s) => s.runtimeChecked);
  const setRuntimeInfo = useConfigStore((s) => s.setRuntimeInfo);
  const rPathOverride = useConfigStore((s) => s.rPathOverride);
  const pixiPathOverride = useConfigStore((s) => s.pixiPathOverride);
  const setRPathOverride = useConfigStore((s) => s.setRPathOverride);
  const setPixiPathOverride = useConfigStore((s) => s.setPixiPathOverride);
  const envStatus = useConfigStore((s) => s.envStatus);
  const setEnvStatus = useConfigStore((s) => s.setEnvStatus);
  const backend = useConfigStore((s) => s.backend);
  const setBackend = useConfigStore((s) => s.setBackend);

  const [deps, setDeps] = useState<DepCheckResult[] | null>(null);
  const [depsLoading, setDepsLoading] = useState(false);
  const [dockerPulling, setDockerPulling] = useState(false);
  const [reinstalling, setReinstalling] = useState(false);

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

  const handleRefreshEnv = async () => {
    try {
      const status = await checkEnv();
      setEnvStatus(status);
    } catch (e) {
      console.error("Env check failed:", e);
    }
  };

  const handleBackendChange = (value: ExecutionBackend) => {
    setBackend(value);
  };

  const handlePullDocker = async () => {
    setDockerPulling(true);
    try {
      await pullDockerImage();
      await handleRefreshEnv();
    } catch (e) {
      console.error("Docker pull failed:", e);
    } finally {
      setDockerPulling(false);
    }
  };

  const handleReinstall = async () => {
    setReinstalling(true);
    try {
      await installEnv();
      await handleRefreshEnv();
    } catch (e) {
      console.error("Reinstall failed:", e);
    } finally {
      setReinstalling(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      <h2 className="text-lg font-semibold">Settings</h2>

      {/* Execution Backend */}
      <section className="border border-border rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-medium">Execution Backend</h3>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="radio"
              name="backend"
              value="local"
              checked={backend === "local"}
              onChange={() => handleBackendChange("local")}
              className="accent-primary"
            />
            <span>Local R</span>
            {envStatus?.rAvailable && envStatus?.packagesOk && (
              <span className="text-xs text-green-600">Ready</span>
            )}
            {envStatus && (!envStatus.rAvailable || !envStatus.packagesOk) && (
              <span className="text-xs text-muted-foreground">Not configured</span>
            )}
          </label>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="radio"
              name="backend"
              value="docker"
              checked={backend === "docker"}
              onChange={() => handleBackendChange("docker")}
              className="accent-primary"
              disabled={!envStatus?.dockerAvailable}
            />
            <span>Docker</span>
            {envStatus?.dockerAvailable && envStatus?.dockerImagePresent && (
              <span className="text-xs text-green-600">Ready</span>
            )}
            {envStatus?.dockerAvailable && !envStatus?.dockerImagePresent && (
              <span className="text-xs text-amber-600">Image not pulled</span>
            )}
            {envStatus && !envStatus.dockerAvailable && (
              <span className="text-xs text-muted-foreground">Not installed</span>
            )}
          </label>
        </div>

        {/* Docker pull button */}
        {backend === "docker" && envStatus?.dockerAvailable && !envStatus?.dockerImagePresent && (
          <button
            onClick={handlePullDocker}
            disabled={dockerPulling}
            className="px-3 py-1.5 text-xs bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors disabled:opacity-50"
          >
            {dockerPulling ? "Pulling..." : "Pull Docker Image"}
          </button>
        )}
      </section>

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

      {/* Environment Management */}
      <section className="border border-border rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-medium">Environment Management</h3>
        <div className="flex items-center gap-3">
          <button
            onClick={handleReinstall}
            disabled={reinstalling}
            className="px-3 py-1.5 text-xs bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors disabled:opacity-50"
          >
            {reinstalling ? "Reinstalling..." : "Reinstall Environment"}
          </button>
          <button
            onClick={handleRefreshEnv}
            className="px-3 py-1.5 text-xs bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
          >
            Refresh Status
          </button>
        </div>
        {envStatus && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center gap-1.5">
              <span className={envStatus.pixiInstalled ? "text-green-600" : "text-destructive"}>
                {envStatus.pixiInstalled ? "\u2713" : "\u2717"}
              </span>
              pixi
            </div>
            <div className="flex items-center gap-1.5">
              <span className={envStatus.rAvailable ? "text-green-600" : "text-destructive"}>
                {envStatus.rAvailable ? "\u2713" : "\u2717"}
              </span>
              R
            </div>
            <div className="flex items-center gap-1.5">
              <span className={envStatus.packagesOk ? "text-green-600" : "text-destructive"}>
                {envStatus.packagesOk ? "\u2713" : "\u2717"}
              </span>
              R Packages
            </div>
            <div className="flex items-center gap-1.5">
              <span className={envStatus.dockerAvailable ? "text-green-600" : "text-muted-foreground"}>
                {envStatus.dockerAvailable ? "\u2713" : "\u2717"}
              </span>
              Docker
            </div>
          </div>
        )}
      </section>

      <section className="border border-border rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-medium">About</h3>
        <div className="text-sm text-muted-foreground space-y-1">
          <p>PROMISE v0.1.0</p>
          <p>PROgnostic Marker Identification and Survival Evaluation</p>
          <p>Cross-platform desktop application powered by Tauri</p>
        </div>
      </section>
    </div>
  );
}

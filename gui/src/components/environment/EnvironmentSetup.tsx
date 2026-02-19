import { useEffect, useRef } from "react";
import { listen } from "@tauri-apps/api/event";
import { useConfigStore } from "@/stores/configStore";
import {
  checkEnv,
  installEnv,
  cancelSetup,
  pullDockerImage,
} from "@/lib/tauri/commands";

export function EnvironmentSetup() {
  const envStatus = useConfigStore((s) => s.envStatus);
  const envChecking = useConfigStore((s) => s.envChecking);
  const setupStatus = useConfigStore((s) => s.setupStatus);
  const setupLogs = useConfigStore((s) => s.setupLogs);
  const setupStep = useConfigStore((s) => s.setupStep);
  const setupError = useConfigStore((s) => s.setupError);
  const setEnvStatus = useConfigStore((s) => s.setEnvStatus);
  const setEnvChecking = useConfigStore((s) => s.setEnvChecking);
  const setSetupStatus = useConfigStore((s) => s.setSetupStatus);
  const appendSetupLog = useConfigStore((s) => s.appendSetupLog);
  const clearSetupLogs = useConfigStore((s) => s.clearSetupLogs);
  const setSetupStep = useConfigStore((s) => s.setSetupStep);
  const setSetupError = useConfigStore((s) => s.setSetupError);
  const setBackend = useConfigStore((s) => s.setBackend);

  const logEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll log
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [setupLogs]);

  // Listen for setup events
  useEffect(() => {
    const unlisten: (() => void)[] = [];

    listen<string>("setup://log", (event) => {
      appendSetupLog(event.payload);
    }).then((u) => unlisten.push(u));

    listen<{ step: number; total: number; message: string }>(
      "setup://progress",
      (event) => {
        const { step, total, message } = event.payload;
        setSetupStep(step, total, message);
      }
    ).then((u) => unlisten.push(u));

    listen<{ success: boolean }>("setup://complete", (event) => {
      if (event.payload.success) {
        setSetupStatus("completed");
        // Re-check env after successful install
        handleCheckEnv();
      } else {
        setSetupStatus("failed");
      }
    }).then((u) => unlisten.push(u));

    return () => {
      unlisten.forEach((u) => u());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Initial env check
  useEffect(() => {
    handleCheckEnv();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCheckEnv = async () => {
    setEnvChecking(true);
    try {
      const status = await checkEnv();
      setEnvStatus(status);
    } catch (e) {
      console.error("Env check failed:", e);
    } finally {
      setEnvChecking(false);
    }
  };

  const handleInstall = async () => {
    clearSetupLogs();
    setSetupStatus("installing");
    setSetupError("");
    try {
      await installEnv();
    } catch (e: unknown) {
      setSetupStatus("failed");
      const msg = typeof e === "string" ? e : (e as Error)?.message ?? "Unknown error";
      setSetupError(msg);
      appendSetupLog(`Error: ${msg}`);
    }
  };

  const handleCancel = async () => {
    try {
      await cancelSetup();
      setSetupStatus("cancelled");
      appendSetupLog("Installation cancelled by user.");
    } catch (e) {
      console.error("Cancel failed:", e);
    }
  };

  const handleUseDocker = async () => {
    setBackend("docker");
    if (envStatus && !envStatus.dockerImagePresent) {
      // Start pulling the image
      clearSetupLogs();
      setSetupStatus("installing");
      setSetupError("");
      try {
        await pullDockerImage();
      } catch (e: unknown) {
        setSetupStatus("failed");
        const msg = typeof e === "string" ? e : (e as Error)?.message ?? "Unknown error";
        setSetupError(msg);
      }
    }
  };

  const isInstalling = setupStatus === "installing";
  const progressPct =
    setupStep.total > 0
      ? Math.round((setupStep.step / setupStep.total) * 100)
      : 0;

  return (
    <div className="flex-1 flex items-center justify-center p-8 bg-background">
      <div className="w-full max-w-lg space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold tracking-tight">PROMISE</h1>
          <p className="text-sm text-muted-foreground">
            PROgnostic Marker Identification and Survival Evaluation
          </p>
        </div>

        {/* Environment Status */}
        <section className="border border-border rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium">Environment Status</h2>
            <button
              onClick={handleCheckEnv}
              disabled={envChecking}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
            >
              {envChecking ? "Checking..." : "Refresh"}
            </button>
          </div>

          {envChecking && !envStatus && (
            <p className="text-xs text-muted-foreground">
              Checking environment...
            </p>
          )}

          {envStatus && (
            <div className="grid grid-cols-3 gap-3 text-xs">
              <StatusItem
                label="pixi"
                ok={envStatus.pixiInstalled}
              />
              <StatusItem
                label="R"
                ok={envStatus.rAvailable}
              />
              <StatusItem
                label="Packages"
                ok={envStatus.packagesOk}
              />
            </div>
          )}
        </section>

        {/* Install / Docker options */}
        <section className="space-y-3">
          {/* Local install button */}
          {!isInstalling && setupStatus !== "completed" && (
            <button
              onClick={handleInstall}
              disabled={isInstalling}
              className="w-full py-2.5 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              Install Analysis Environment
            </button>
          )}
          {!isInstalling && setupStatus !== "completed" && (
            <p className="text-xs text-center text-muted-foreground">
              Installs pixi, R, and required packages (~10-15 minutes)
            </p>
          )}

          {/* Cancel button during install */}
          {isInstalling && (
            <button
              onClick={handleCancel}
              className="w-full py-2.5 text-sm font-medium bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors"
            >
              Cancel Installation
            </button>
          )}

          {/* Docker option */}
          {envStatus?.dockerAvailable && (
            <>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <div className="flex-1 border-t border-border" />
                <span>or</span>
                <div className="flex-1 border-t border-border" />
              </div>
              <div className="flex items-center justify-between">
                <div className="text-xs space-y-0.5">
                  <span className="text-green-600">Docker detected</span>
                  {envStatus.dockerImagePresent && (
                    <span className="ml-2 text-muted-foreground">
                      (image ready)
                    </span>
                  )}
                </div>
                <button
                  onClick={handleUseDocker}
                  disabled={isInstalling}
                  className="px-4 py-1.5 text-xs bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors disabled:opacity-50"
                >
                  Use Docker Instead
                </button>
              </div>
            </>
          )}
        </section>

        {/* Setup completed message */}
        {setupStatus === "completed" && (
          <div className="border border-green-500/30 bg-green-500/5 rounded-lg p-3 text-center">
            <p className="text-sm text-green-600 font-medium">
              Environment ready! Starting PROMISE...
            </p>
          </div>
        )}

        {/* Error message */}
        {setupError && (
          <div className="border border-destructive/30 bg-destructive/5 rounded-lg p-3">
            <p className="text-xs text-destructive">{setupError}</p>
          </div>
        )}

        {/* Install log */}
        {setupLogs.length > 0 && (
          <section className="border border-border rounded-lg overflow-hidden">
            {/* Progress bar */}
            {isInstalling && setupStep.total > 0 && (
              <div className="px-3 py-2 border-b border-border bg-muted/30 space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span>{setupStep.message}</span>
                  <span className="text-muted-foreground">
                    Step {setupStep.step}/{setupStep.total} ({progressPct}%)
                  </span>
                </div>
                <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all duration-300"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>
              </div>
            )}

            {/* Log output */}
            <div className="max-h-48 overflow-y-auto p-3 bg-muted/10">
              {setupLogs.map((line, i) => (
                <p key={i} className="text-[11px] font-mono text-muted-foreground leading-relaxed">
                  {line}
                </p>
              ))}
              <div ref={logEndRef} />
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

function StatusItem({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center gap-1.5 text-xs">
      <span className={ok ? "text-green-600" : "text-muted-foreground"}>
        {ok ? "\u2713" : "\u2717"}
      </span>
      <span>{label}</span>
    </div>
  );
}

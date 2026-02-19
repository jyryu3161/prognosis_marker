import { useState, useEffect } from "react";
import { listen } from "@tauri-apps/api/event";
import { Sidebar, type Page } from "@/components/layout/Sidebar";
import { SetupPage } from "@/pages/SetupPage";
import { ResultsPage } from "@/pages/ResultsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { useAnalysisStore } from "@/stores/analysisStore";
import { useConfigStore } from "@/stores/configStore";
import { detectRuntime } from "@/lib/tauri/commands";

function App() {
  const [currentPage, setCurrentPage] = useState<Page>("setup");
  const status = useAnalysisStore((s) => s.status);
  const setRuntimeInfo = useConfigStore((s) => s.setRuntimeInfo);

  const hasResults =
    status === "completed" || status === "running" || status === "failed";

  // Warn before closing if analysis is running
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (useAnalysisStore.getState().status === "running") {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, []);

  // Detect R runtime on startup
  useEffect(() => {
    detectRuntime()
      .then(setRuntimeInfo)
      .catch((e) => console.error("Runtime detection failed:", e));
  }, [setRuntimeInfo]);

  // Listen for analysis events from Rust backend
  useEffect(() => {
    const unlisten: (() => void)[] = [];

    listen<{ success: boolean; code: number | null }>(
      "analysis://complete",
      (event) => {
        const { success, code } = event.payload;
        const store = useAnalysisStore.getState();
        if (store.status === "cancelled") {
          store.appendLog(`Analysis cancelled by user (exit code ${code})`);
          return;
        }
        store.appendLog(
          success
            ? `Analysis completed successfully (exit code ${code})`
            : `Analysis finished with exit code ${code}`,
        );
        if (!success) {
          store.setParam("errorMessage", `Exit code ${code}. Check Results > Log for details.`);
        }
        store.setStatus(success ? "completed" : "failed");
      },
    ).then((u) => unlisten.push(u));

    listen<{ message: string }>("analysis://error", (event) => {
      const store = useAnalysisStore.getState();
      if (store.status === "cancelled") return;
      store.appendLog(`Error: ${event.payload.message}`);
      store.setParam("errorMessage", event.payload.message);
      store.setStatus("failed");
    }).then((u) => unlisten.push(u));

    listen<string>("analysis://log", (event) => {
      useAnalysisStore.getState().appendLog(event.payload);
    }).then((u) => unlisten.push(u));

    listen<{ type: string; current: number; total: number; message: string }>(
      "analysis://progress",
      (event) => {
        const { type, current, total, message } = event.payload;
        const store = useAnalysisStore.getState();
        const prev = store.progress;
        if (type === "total") {
          store.setProgress(0, total, message);
        } else if (type === "iteration_complete") {
          store.setProgress(current, prev.total || total, message);
        } else {
          store.setProgress(current, total || prev.total, message);
        }
      },
    ).then((u) => unlisten.push(u));

    return () => {
      unlisten.forEach((u) => u());
    };
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      <Sidebar
        currentPage={currentPage}
        onPageChange={setCurrentPage}
        analysisRunning={hasResults}
      />
      <main className="flex-1 flex flex-col overflow-hidden">
        {currentPage === "setup" && <SetupPage />}
        {currentPage === "results" && <ResultsPage />}
        {currentPage === "settings" && <SettingsPage />}
      </main>
    </div>
  );
}

export default App;

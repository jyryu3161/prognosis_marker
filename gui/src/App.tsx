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
  const setStatus = useAnalysisStore((s) => s.setStatus);
  const appendLog = useAnalysisStore((s) => s.appendLog);
  const setProgress = useAnalysisStore((s) => s.setProgress);
  const setRuntimeInfo = useConfigStore((s) => s.setRuntimeInfo);

  const hasResults =
    status === "completed" || status === "running" || status === "failed";

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
        appendLog(
          success
            ? `Analysis completed successfully (exit code ${code})`
            : `Analysis finished with exit code ${code}`,
        );
        setStatus(success ? "completed" : "failed");
      },
    ).then((u) => unlisten.push(u));

    listen<{ message: string }>("analysis://error", (event) => {
      appendLog(`Error: ${event.payload.message}`);
      setStatus("failed");
    }).then((u) => unlisten.push(u));

    listen<string>("analysis://log", (event) => {
      appendLog(event.payload);
    }).then((u) => unlisten.push(u));

    listen<{ type: string; current: number; total: number; message: string }>(
      "analysis://progress",
      (event) => {
        const { current, total, message } = event.payload;
        setProgress(current, total, message);
      },
    ).then((u) => unlisten.push(u));

    return () => unlisten.forEach((u) => u());
  }, [setStatus, appendLog, setProgress]);

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

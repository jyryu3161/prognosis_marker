import { useState, useEffect } from "react";
import { useAnalysisStore } from "@/stores/analysisStore";
import { readImageBase64, listOutputPlots } from "@/lib/tauri/commands";
import { AucTable } from "@/components/results/AucTable";

function LogPanel() {
  const logs = useAnalysisStore((s) => s.logs);
  const status = useAnalysisStore((s) => s.status);
  const progress = useAnalysisStore((s) => s.progress);

  return (
    <div className="border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium">Execution Log</h3>
        {status === "running" && progress.total > 0 && (
          <div className="flex items-center gap-3">
            <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-300"
                style={{
                  width: `${Math.round((progress.current / progress.total) * 100)}%`,
                }}
              />
            </div>
            <span className="text-xs text-muted-foreground font-mono">
              {progress.current}/{progress.total} — {progress.message}
            </span>
          </div>
        )}
      </div>
      <div className="bg-muted/30 rounded p-3 h-48 overflow-y-auto font-mono text-xs space-y-0.5">
        {logs.length === 0 ? (
          <p className="text-muted-foreground">No log output yet.</p>
        ) : (
          logs.map((line, i) => (
            <div key={i} className="text-muted-foreground whitespace-pre-wrap">
              {line}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function PlotViewer({ outputDir }: { outputDir: string }) {
  const [plots, setPlots] = useState<string[]>([]);
  const [selectedPlot, setSelectedPlot] = useState<string | null>(null);
  const [imageData, setImageData] = useState<string | null>(null);

  useEffect(() => {
    if (!outputDir) return;

    listOutputPlots(outputDir)
      .then((files) => {
        setPlots(files);
        // Auto-select first PNG
        const firstPng = files.find((f) => f.endsWith(".png"));
        if (firstPng) setSelectedPlot(firstPng);
      })
      .catch(() => {
        // Fallback to hardcoded names if command fails
        setPlots([
          "ROC_curve.png",
          "importance.png",
          "kaplan_meier.png",
          "time_dependent_AUC.png",
          "DCA.png",
        ]);
      });
  }, [outputDir]);

  useEffect(() => {
    if (!selectedPlot || !outputDir) {
      setImageData(null);
      return;
    }
    const path = `${outputDir}/${selectedPlot}`;
    readImageBase64(path)
      .then((data) => {
        const ext = selectedPlot.split(".").pop()?.toLowerCase();
        const mime =
          ext === "tiff" ? "image/tiff" : ext === "svg" ? "image/svg+xml" : "image/png";
        setImageData(`data:${mime};base64,${data}`);
      })
      .catch(() => setImageData(null));
  }, [selectedPlot, outputDir]);

  // Group by category for tab display
  const plotCategories = categorize(plots);

  return (
    <div className="border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium mb-3">Plots</h3>

      {/* Tab-style plot selector */}
      <div className="flex gap-1 flex-wrap mb-3 border-b border-border pb-2">
        {plotCategories.map(({ label, files }) => (
          <div key={label} className="flex gap-1">
            {files.map((plot) => (
              <button
                key={plot}
                onClick={() => setSelectedPlot(plot)}
                className={`px-3 py-1.5 text-xs rounded-t-md transition-colors ${
                  selectedPlot === plot
                    ? "bg-primary/10 text-primary border-b-2 border-primary font-medium"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                }`}
              >
                {plot.replace(/\.(png|tiff|svg|pdf)$/, "")}
              </button>
            ))}
          </div>
        ))}
      </div>

      <div className="bg-muted/20 rounded min-h-[300px] flex items-center justify-center">
        {imageData ? (
          <img
            src={imageData}
            alt={selectedPlot ?? "plot"}
            className="max-w-full max-h-[500px] object-contain"
          />
        ) : (
          <p className="text-sm text-muted-foreground">
            {selectedPlot ? "Loading plot..." : "Select a plot to view"}
          </p>
        )}
      </div>
    </div>
  );
}

function categorize(plots: string[]): { label: string; files: string[] }[] {
  const categories: Record<string, string[]> = {};
  for (const plot of plots) {
    const name = plot.replace(/\.(png|tiff|svg|pdf)$/, "").toLowerCase();
    let cat = "other";
    if (name.includes("roc")) cat = "ROC";
    else if (name.includes("importance")) cat = "Importance";
    else if (name.includes("kaplan") || name.includes("km")) cat = "KM";
    else if (name.includes("auc") || name.includes("time_dependent")) cat = "Time AUC";
    else if (name.includes("dca")) cat = "DCA";

    if (!categories[cat]) categories[cat] = [];
    categories[cat].push(plot);
  }
  return Object.entries(categories).map(([label, files]) => ({ label, files }));
}

export function ResultsPage() {
  const status = useAnalysisStore((s) => s.status);
  const outputDir = useAnalysisStore((s) => s.outputDir);

  const hasRun = status === "completed" || status === "running" || status === "failed";

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      <h2 className="text-lg font-semibold">Results</h2>

      {!hasRun ? (
        <div className="border border-border rounded-lg p-8 text-center">
          <p className="text-muted-foreground">
            Run an analysis to see results here.
          </p>
        </div>
      ) : (
        <>
          <LogPanel />
          {status === "completed" && (
            <>
              <PlotViewer outputDir={outputDir} />
              <AucTable outputDir={outputDir} />
            </>
          )}
        </>
      )}
    </div>
  );
}

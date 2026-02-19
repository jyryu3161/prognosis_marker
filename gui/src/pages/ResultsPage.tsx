import { useState, useEffect, useRef } from "react";
import { useAnalysisStore } from "@/stores/analysisStore";
import {
  readImageBase64,
  listOutputPlots,
  saveFile,
  openDirectory,
} from "@/lib/tauri/commands";
import { AucTable } from "@/components/results/AucTable";

function LogPanel() {
  const logs = useAnalysisStore((s) => s.logs);
  const status = useAnalysisStore((s) => s.status);
  const progress = useAnalysisStore((s) => s.progress);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

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
        <div ref={logEndRef} />
      </div>
    </div>
  );
}

/** Group plot files by stem name (e.g., Binary_ROCcurve → {svg, tiff}) */
function groupByName(
  allFiles: string[],
): { name: string; label: string; formats: { ext: string; relPath: string }[] }[] {
  const map = new Map<string, { ext: string; relPath: string }[]>();

  for (const f of allFiles) {
    const basename = f.replace(/^.*\//, "");
    const dotIdx = basename.lastIndexOf(".");
    if (dotIdx === -1) continue;
    const stem = basename.slice(0, dotIdx);
    const ext = basename.slice(dotIdx + 1).toLowerCase();
    if (!map.has(stem)) map.set(stem, []);
    map.get(stem)!.push({ ext, relPath: f });
  }

  return Array.from(map.entries()).map(([stem, formats]) => ({
    name: stem,
    label: stem.replace(/^Binary_|^Survival_/i, "").replace(/_/g, " "),
    formats: formats.sort((a, b) => {
      // SVG first, then PNG, then TIFF, then PDF
      const order: Record<string, number> = { svg: 0, png: 1, tiff: 2, pdf: 3 };
      return (order[a.ext] ?? 9) - (order[b.ext] ?? 9);
    }),
  }));
}

function PlotViewer({
  outputDir,
  allFiles,
}: {
  outputDir: string;
  allFiles: string[];
}) {
  const [selectedPlot, setSelectedPlot] = useState<string | null>(null);
  const [imageData, setImageData] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Displayable files: SVG and PNG only (TIFF can't render in browser)
  const displayable = allFiles.filter(
    (f) => f.endsWith(".svg") || f.endsWith(".png"),
  );

  const plotCategories = categorize(displayable);

  // Auto-select first plot
  useEffect(() => {
    if (displayable.length > 0 && !selectedPlot) {
      setSelectedPlot(displayable[0]);
    }
  }, [displayable.length]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!selectedPlot || !outputDir) {
      setImageData(null);
      return;
    }
    const path = `${outputDir}/${selectedPlot}`;
    setError(null);
    readImageBase64(path)
      .then((data: string) => {
        const ext = selectedPlot.split(".").pop()?.toLowerCase();
        const mime =
          ext === "svg" ? "image/svg+xml" : "image/png";
        setImageData(`data:${mime};base64,${data}`);
      })
      .catch((e: unknown) => {
        setError(`Failed to load: ${e}`);
        setImageData(null);
      });
  }, [selectedPlot, outputDir]);

  if (displayable.length === 0) return null;

  return (
    <div className="border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium mb-3">Plot Preview</h3>

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
                {plot
                  .replace(/^.*\//, "")
                  .replace(/\.(png|tiff|svg|pdf)$/, "")
                  .replace(/^Binary_|^Survival_/i, "")
                  .replace(/_/g, " ")}
              </button>
            ))}
          </div>
        ))}
      </div>

      {error && <p className="text-xs text-destructive mb-2">{error}</p>}

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

function ExportPanel({ outputDir, allFiles }: { outputDir: string; allFiles: string[] }) {
  const [saving, setSaving] = useState<string | null>(null);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  const groups = groupByName(allFiles);

  const handleSave = async (relPath: string) => {
    const filename = relPath.replace(/^.*\//, "");
    const sourcePath = `${outputDir}/${relPath}`;
    setSaving(relPath);
    setSavedMsg(null);
    try {
      const dest = await saveFile(sourcePath, filename);
      if (dest) {
        setSavedMsg(`Saved: ${dest}`);
      }
    } catch (e) {
      setSavedMsg(`Error: ${e}`);
    } finally {
      setSaving(null);
    }
  };

  const handleOpenFolder = async () => {
    const figDir = `${outputDir}/figures`;
    try {
      await openDirectory(figDir);
    } catch {
      await openDirectory(outputDir);
    }
  };

  if (groups.length === 0) return null;

  return (
    <div className="border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium">Export Figures</h3>
        <button
          onClick={handleOpenFolder}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
        >
          Open Folder
        </button>
      </div>

      {savedMsg && (
        <p
          className={`text-xs mb-2 ${savedMsg.startsWith("Error") ? "text-destructive" : "text-green-600"}`}
        >
          {savedMsg}
        </p>
      )}

      <div className="space-y-1">
        <div className="grid grid-cols-[1fr_auto] gap-2 items-center text-xs text-muted-foreground font-medium px-2 pb-1 border-b border-border">
          <span>Figure</span>
          <span>Save As</span>
        </div>

        {groups.map(({ name, label, formats }) => (
          <div
            key={name}
            className="grid grid-cols-[1fr_auto] gap-2 items-center px-2 py-1.5 rounded hover:bg-muted/30"
          >
            <span className="text-sm truncate" title={name}>
              {label}
            </span>
            <div className="flex gap-1.5">
              {formats.map(({ ext, relPath }) => (
                <button
                  key={ext}
                  onClick={() => handleSave(relPath)}
                  disabled={saving === relPath}
                  className={`px-2.5 py-1 text-xs font-medium rounded border transition-colors ${
                    ext === "svg"
                      ? "border-blue-300 text-blue-700 hover:bg-blue-50 dark:border-blue-700 dark:text-blue-400 dark:hover:bg-blue-950"
                      : ext === "tiff"
                        ? "border-amber-300 text-amber-700 hover:bg-amber-50 dark:border-amber-700 dark:text-amber-400 dark:hover:bg-amber-950"
                        : ext === "png"
                          ? "border-green-300 text-green-700 hover:bg-green-50 dark:border-green-700 dark:text-green-400 dark:hover:bg-green-950"
                          : "border-border text-muted-foreground hover:bg-muted/50"
                  } disabled:opacity-50`}
                  title={ext === "tiff" ? "TIFF 300 DPI (publication quality)" : ext.toUpperCase()}
                >
                  {saving === relPath ? "..." : ext.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-muted-foreground mt-3">
        SVG: scalable vector / TIFF: 300 DPI raster (publication-ready)
      </p>
    </div>
  );
}

function categorize(plots: string[]): { label: string; files: string[] }[] {
  const categories: Record<string, string[]> = {};
  for (const plot of plots) {
    const basename = plot
      .replace(/^.*\//, "")
      .replace(/\.(png|tiff|svg|pdf)$/, "")
      .toLowerCase();
    let cat = "Other";
    if (basename.includes("roc")) cat = "ROC";
    else if (basename.includes("importance")) cat = "Importance";
    else if (basename.includes("kaplan") || basename.includes("km")) cat = "KM";
    else if (basename.includes("auc") || basename.includes("time_dependent")) cat = "AUC";
    else if (basename.includes("dca")) cat = "DCA";
    else if (basename.includes("stepwise") || basename.includes("process"))
      cat = "Stepwise";

    if (!categories[cat]) categories[cat] = [];
    categories[cat].push(plot);
  }
  return Object.entries(categories).map(([label, files]) => ({ label, files }));
}

export function ResultsPage() {
  const status = useAnalysisStore((s) => s.status);
  const outputDir = useAnalysisStore((s) => s.outputDir);
  const [allFiles, setAllFiles] = useState<string[]>([]);

  const hasRun =
    status === "completed" || status === "running" || status === "failed";
  const showPlots = status === "completed" || (status !== "running" && outputDir);

  // Clear previous plots when a new analysis starts; reload when complete
  useEffect(() => {
    if (status === "running") {
      setAllFiles([]);
      return;
    }
    if (!outputDir) {
      setAllFiles([]);
      return;
    }
    listOutputPlots(outputDir)
      .then(setAllFiles)
      .catch(() => setAllFiles([]));
  }, [outputDir, status]);

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      <h2 className="text-lg font-semibold">Results</h2>

      {hasRun && <LogPanel />}

      {showPlots && outputDir ? (
        <>
          <PlotViewer outputDir={outputDir} allFiles={allFiles} />
          <ExportPanel outputDir={outputDir} allFiles={allFiles} />
          <AucTable outputDir={outputDir} />
        </>
      ) : !hasRun ? (
        <div className="border border-border rounded-lg p-8 text-center">
          <p className="text-muted-foreground">
            Run an analysis to see results here.
          </p>
        </div>
      ) : null}
    </div>
  );
}

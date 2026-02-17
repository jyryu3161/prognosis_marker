import { useAnalysisStore } from "@/stores/analysisStore";
import { pickFile } from "@/lib/tauri/commands";
import type { PAdjustMethod } from "@/types/analysis";

function Checkbox({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="w-4 h-4 rounded border-border accent-primary cursor-pointer"
      />
      <span className="text-sm">{label}</span>
    </label>
  );
}

export function AdvancedOptionsSection() {
  const enablePValueFilter = useAnalysisStore((s) => s.enablePValueFilter);
  const pAdjustMethod = useAnalysisStore((s) => s.pAdjustMethod);
  const pThreshold = useAnalysisStore((s) => s.pThreshold);
  const topK = useAnalysisStore((s) => s.topK);
  const enableEvidence = useAnalysisStore((s) => s.enableEvidence);
  const evidenceGeneFile = useAnalysisStore((s) => s.evidenceGeneFile);
  const evidenceScoreThreshold = useAnalysisStore((s) => s.evidenceScoreThreshold);
  const setParam = useAnalysisStore((s) => s.setParam);

  const handlePickEvidenceFile = async () => {
    try {
      const path = await pickFile();
      if (path) setParam("evidenceGeneFile", path);
    } catch (e) {
      console.error("File pick error:", e);
    }
  };

  return (
    <section className="border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium mb-3">Advanced Options</h3>

      <div className="space-y-4">
        {/* P-value filtering */}
        <div className="space-y-3">
          <Checkbox
            label="Enable P-value filtering"
            checked={enablePValueFilter}
            onChange={(v) => setParam("enablePValueFilter", v)}
          />

          {enablePValueFilter && (
            <div className="ml-6 space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-medium text-muted-foreground">
                    Adjustment Method
                  </label>
                  <select
                    value={pAdjustMethod}
                    onChange={(e) =>
                      setParam("pAdjustMethod", e.target.value as PAdjustMethod)
                    }
                    className="h-9 px-3 rounded-md border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="fdr">FDR (BH)</option>
                    <option value="bonferroni">Bonferroni</option>
                    <option value="none">None</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-xs font-medium text-muted-foreground">
                    P-value Threshold
                  </label>
                  <input
                    type="number"
                    value={pThreshold}
                    min={0.001}
                    max={1}
                    step={0.01}
                    onChange={(e) => setParam("pThreshold", Number(e.target.value))}
                    className="h-9 px-3 rounded-md border border-border bg-background text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-xs font-medium text-muted-foreground">
                    Top K Genes
                  </label>
                  <input
                    type="number"
                    value={topK ?? ""}
                    min={1}
                    max={10000}
                    placeholder="All"
                    onChange={(e) =>
                      setParam("topK", e.target.value ? Number(e.target.value) : null)
                    }
                    className="h-9 px-3 rounded-md border border-border bg-background text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Evidence-based filtering */}
        <div className="space-y-3 pt-2 border-t border-border">
          <Checkbox
            label="Use evidence-based gene filtering (Open Targets)"
            checked={enableEvidence}
            onChange={(v) => setParam("enableEvidence", v)}
          />

          {enableEvidence && (
            <div className="ml-6 space-y-3">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-muted-foreground">
                  Evidence Gene File
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={evidenceGeneFile}
                    onChange={(e) => setParam("evidenceGeneFile", e.target.value)}
                    placeholder="Select evidence gene file..."
                    className="flex-1 h-9 px-3 rounded-md border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  <button
                    onClick={handlePickEvidenceFile}
                    className="px-3 py-2 bg-secondary text-secondary-foreground rounded-md text-sm hover:bg-secondary/80 transition-colors whitespace-nowrap"
                  >
                    Browse
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-1 max-w-xs">
                <label className="text-xs font-medium text-muted-foreground">
                  Score Threshold
                </label>
                <input
                  type="number"
                  value={evidenceScoreThreshold}
                  min={0}
                  max={1}
                  step={0.01}
                  onChange={(e) =>
                    setParam("evidenceScoreThreshold", Number(e.target.value))
                  }
                  className="h-9 px-3 rounded-md border border-border bg-background text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

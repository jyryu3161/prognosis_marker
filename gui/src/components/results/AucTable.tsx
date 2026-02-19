import { useState, useEffect } from "react";

interface AucRow {
  iteration: number;
  trainAuc: number;
  testAuc: number;
  genes: string;
}

export function AucTable({ outputDir }: { outputDir: string }) {
  const [rows, setRows] = useState<AucRow[]>([]);

  useEffect(() => {
    if (!outputDir) return;
    // AUC data would be loaded from the output directory
    // For now, show placeholder until analysis produces CSV
    setRows([]);
  }, [outputDir]);

  if (rows.length === 0) {
    return (
      <div className="border border-border rounded-lg p-4">
        <h3 className="text-sm font-medium mb-2">AUC Summary</h3>
        <p className="text-xs text-muted-foreground">
          AUC iteration data will appear here after analysis completes.
        </p>
      </div>
    );
  }

  return (
    <div className="border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium mb-3">AUC Summary</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-muted/50">
              <th className="px-3 py-2 text-left font-medium">Iteration</th>
              <th className="px-3 py-2 text-left font-medium">Train AUC</th>
              <th className="px-3 py-2 text-left font-medium">Test AUC</th>
              <th className="px-3 py-2 text-left font-medium">Selected Genes</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.iteration} className="border-t border-border">
                <td className="px-3 py-2 font-mono">{row.iteration}</td>
                <td className="px-3 py-2 font-mono">{row.trainAuc.toFixed(4)}</td>
                <td className="px-3 py-2 font-mono">{row.testAuc.toFixed(4)}</td>
                <td className="px-3 py-2 text-muted-foreground truncate max-w-xs">
                  {row.genes}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

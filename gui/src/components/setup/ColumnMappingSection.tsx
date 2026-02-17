import { useAnalysisStore } from "@/stores/analysisStore";

function ColumnSelect({
  label,
  value,
  columns,
  onChange,
  optional = false,
}: {
  label: string;
  value: string;
  columns: string[];
  onChange: (v: string) => void;
  optional?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-muted-foreground">
        {label}
        {optional && <span className="ml-1 text-muted-foreground/60">(optional)</span>}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 px-3 rounded-md border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
      >
        <option value="">Select column...</option>
        {columns.map((col) => (
          <option key={col} value={col}>
            {col}
          </option>
        ))}
      </select>
    </div>
  );
}

export function ColumnMappingSection() {
  const analysisType = useAnalysisStore((s) => s.analysisType);
  const dataInfo = useAnalysisStore((s) => s.dataInfo);
  const sampleId = useAnalysisStore((s) => s.sampleId);
  const outcome = useAnalysisStore((s) => s.outcome);
  const event = useAnalysisStore((s) => s.event);
  const timeVariable = useAnalysisStore((s) => s.timeVariable);
  const setColumnMapping = useAnalysisStore((s) => s.setColumnMapping);

  const columns = dataInfo?.columns ?? [];

  return (
    <section className="border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium mb-3">Column Mapping</h3>

      {columns.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Load a CSV file first to map columns.
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <ColumnSelect
            label="Sample ID"
            value={sampleId}
            columns={columns}
            onChange={(v) => setColumnMapping("sampleId", v)}
          />

          {analysisType === "binary" ? (
            <ColumnSelect
              label="Outcome (0/1)"
              value={outcome}
              columns={columns}
              onChange={(v) => setColumnMapping("outcome", v)}
            />
          ) : (
            <ColumnSelect
              label="Event (0/1)"
              value={event}
              columns={columns}
              onChange={(v) => setColumnMapping("event", v)}
            />
          )}

          <ColumnSelect
            label="Time Variable"
            value={timeVariable}
            columns={columns}
            onChange={(v) => setColumnMapping("timeVariable", v)}
            optional={analysisType === "binary"}
          />
        </div>
      )}
    </section>
  );
}

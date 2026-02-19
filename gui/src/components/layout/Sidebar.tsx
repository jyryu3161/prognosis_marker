import { cn } from "@/lib/utils";

export type Page = "setup" | "results" | "settings";

interface SidebarProps {
  currentPage: Page;
  onPageChange: (page: Page) => void;
  analysisRunning: boolean;
}

const navItems: { id: Page; label: string; icon: string }[] = [
  { id: "setup", label: "Setup", icon: "⚙️" },
  { id: "results", label: "Results", icon: "📊" },
  { id: "settings", label: "Settings", icon: "🔧" },
];

export function Sidebar({ currentPage, onPageChange, analysisRunning }: SidebarProps) {
  return (
    <aside className="w-48 border-r border-border bg-secondary/30 flex flex-col">
      <div className="p-4 border-b border-border">
        <h1 className="text-sm font-bold text-primary">PROMISE</h1>
        <p className="text-xs text-muted-foreground mt-0.5">PROgnostic Marker Identification and Survival Evaluation</p>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onPageChange(item.id)}
            className={cn(
              "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors text-left",
              currentPage === item.id
                ? "bg-primary text-primary-foreground"
                : "hover:bg-accent text-foreground",
            )}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
            {item.id === "results" && analysisRunning && (
              <span className="ml-auto w-2 h-2 rounded-full bg-green-500" />
            )}
          </button>
        ))}
      </nav>
      <div className="p-3 border-t border-border text-xs text-muted-foreground">
        v0.1.0
      </div>
    </aside>
  );
}

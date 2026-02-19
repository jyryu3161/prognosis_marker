import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AnalysisTypeSelector } from "@/components/setup/AnalysisTypeSelector";
import { Sidebar } from "@/components/layout/Sidebar";

describe("AnalysisTypeSelector", () => {
  it("renders binary and survival options", () => {
    const onChange = vi.fn();
    render(<AnalysisTypeSelector value="binary" onChange={onChange} />);

    expect(screen.getByText("Binary Classification")).toBeDefined();
    expect(screen.getByText("Survival Analysis")).toBeDefined();
  });

  it("calls onChange when clicking survival option", () => {
    const onChange = vi.fn();
    render(<AnalysisTypeSelector value="binary" onChange={onChange} />);

    fireEvent.click(screen.getByText("Survival Analysis"));
    expect(onChange).toHaveBeenCalledWith("survival");
  });

  it("calls onChange when clicking binary option", () => {
    const onChange = vi.fn();
    render(<AnalysisTypeSelector value="survival" onChange={onChange} />);

    fireEvent.click(screen.getByText("Binary Classification"));
    expect(onChange).toHaveBeenCalledWith("binary");
  });

  it("shows description for each option", () => {
    const onChange = vi.fn();
    render(<AnalysisTypeSelector value="binary" onChange={onChange} />);

    expect(screen.getByText(/Logistic regression/)).toBeDefined();
    expect(screen.getByText(/Cox regression/)).toBeDefined();
  });
});

describe("Sidebar", () => {
  it("renders all navigation items", () => {
    const onPageChange = vi.fn();
    render(<Sidebar currentPage="setup" onPageChange={onPageChange} analysisRunning={false} />);

    expect(screen.getByText("Setup")).toBeDefined();
    expect(screen.getByText("Results")).toBeDefined();
    expect(screen.getByText("Settings")).toBeDefined();
  });

  it("calls onPageChange when clicking a nav item", () => {
    const onPageChange = vi.fn();
    render(<Sidebar currentPage="setup" onPageChange={onPageChange} analysisRunning={false} />);

    fireEvent.click(screen.getByText("Settings"));
    expect(onPageChange).toHaveBeenCalledWith("settings");
  });

  it("shows app title and version", () => {
    const onPageChange = vi.fn();
    render(<Sidebar currentPage="setup" onPageChange={onPageChange} analysisRunning={false} />);

    expect(screen.getByText("PROMISE")).toBeDefined();
    expect(screen.getByText("v0.1.0")).toBeDefined();
  });

  it("shows running indicator when analysis is active", () => {
    const onPageChange = vi.fn();
    const { container } = render(
      <Sidebar currentPage="setup" onPageChange={onPageChange} analysisRunning={true} />,
    );

    // The running indicator is a green dot next to Results
    const greenDot = container.querySelector(".bg-green-500");
    expect(greenDot).toBeTruthy();
  });
});

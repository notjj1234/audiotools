import { act, type ReactNode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { progressFraction } from "./components/JobProgress";
import { useHeldVisible } from "./pending";

(globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
  true;

describe("progressFraction", () => {
  it("ignores missing or non-finite percents", () => {
    expect(progressFraction(undefined)).toBeNull();
    expect(progressFraction(null)).toBeNull();
    expect(progressFraction(Number.NaN)).toBeNull();
    expect(progressFraction(Number.POSITIVE_INFINITY)).toBeNull();
  });

  it("reads a 0–1 fraction and a 0–100 percent", () => {
    expect(progressFraction(0)).toBe(0);
    expect(progressFraction(0.5)).toBe(0.5);
    expect(progressFraction(1)).toBe(1);
    expect(progressFraction(50)).toBe(0.5);
    expect(progressFraction(100)).toBe(1);
    expect(progressFraction(-4)).toBe(0);
    expect(progressFraction(140)).toBe(1);
  });
});

function Probe({ active }: { active: boolean }) {
  const shown = useHeldVisible(active, 200, 500);
  return <span>{shown ? "shown" : "hidden"}</span>;
}

describe("useHeldVisible", () => {
  let root: Root | null = null;
  let host: HTMLDivElement | null = null;

  afterEach(() => {
    act(() => root?.unmount());
    host?.remove();
    root = null;
    host = null;
    vi.useRealTimers();
  });

  async function render(node: ReactNode) {
    host = document.createElement("div");
    document.body.appendChild(host);
    root = createRoot(host);
    await act(async () => {
      root?.render(node);
    });
    return host;
  }

  it("waits 200ms to appear and stays at least 500ms", async () => {
    vi.useFakeTimers();
    const view = await render(<Probe active />);
    expect(view.textContent).toBe("hidden");
    await act(async () => {
      vi.advanceTimersByTime(199);
    });
    expect(view.textContent).toBe("hidden");
    await act(async () => {
      vi.advanceTimersByTime(1);
    });
    expect(view.textContent).toBe("shown");
    await act(async () => {
      root?.render(<Probe active={false} />);
    });
    await act(async () => {
      vi.advanceTimersByTime(499);
    });
    expect(view.textContent).toBe("shown");
    await act(async () => {
      vi.advanceTimersByTime(1);
    });
    expect(view.textContent).toBe("hidden");
  });

  it("skips the cue when the wait ends before 200ms", async () => {
    vi.useFakeTimers();
    const view = await render(<Probe active />);
    await act(async () => {
      root?.render(<Probe active={false} />);
    });
    await act(async () => {
      vi.advanceTimersByTime(500);
    });
    expect(view.textContent).toBe("hidden");
  });
});

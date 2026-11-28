import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { colorTokenToCustomVar } from "./ThemeContext";

const webRoot = process.cwd();

function readSource(rel: string): string {
  return readFileSync(resolve(webRoot, rel), "utf-8");
}

describe("ThemeContext custom token mapping", () => {
  it("maps --color-* to --custom-* (not --custom-color-*)", () => {
    expect(colorTokenToCustomVar("--color-accent-primary")).toBe("--custom-accent-primary");
    expect(colorTokenToCustomVar("--color-bg-deep")).toBe("--custom-bg-deep");
    expect(colorTokenToCustomVar("--custom-accent-primary")).toBe("--custom-accent-primary");
  });

  it("clears custom tokens when leaving the custom preset", () => {
    const src = readSource("src/theme/ThemeContext.tsx");
    expect(src).toContain("setCustomTokens({})");
    expect(src).toContain("removeProperty");
    expect(src).toContain("colorTokenToCustomVar");
  });

  it("derives light/dark mode from named presets", () => {
    const src = readSource("src/theme/ThemeContext.tsx");
    expect(src).toContain("modeFromPresetId");
    expect(src).toContain("setMode(fromName)");
  });
});

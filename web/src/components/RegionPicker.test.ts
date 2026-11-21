import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const src = readFileSync(resolve(process.cwd(), "src/components/RegionPicker.tsx"), "utf-8");

describe("RegionPicker play control", () => {
  it("enables Play from ready state instead of hardcoding disabled", () => {
    expect(src).toContain("disabled={!ready}");
    expect(src).not.toMatch(/disabled\s*\n\s*onClick=\{togglePlay\}/);
  });

  it("only restarts region playback when already playing", () => {
    expect(src).toContain("if (ws.isPlaying())");
    expect(src).toContain("region.play(true)");
  });
});

import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const isolate = readFileSync(resolve(process.cwd(), "src/pages/IsolatePage.tsx"), "utf-8");
const tab = readFileSync(resolve(process.cwd(), "src/pages/TabPage.tsx"), "utf-8");

describe("job watch cleanup", () => {
  it("IsolatePage stops watchJob on unmount and clears clipLabel on queue select", () => {
    expect(isolate).toContain("stopWatchRef.current?.()");
    expect(isolate).toContain("setClipLabel(null)");
  });

  it("TabPage stops watchJob on unmount", () => {
    expect(tab).toContain("stopWatchRef.current?.()");
  });
});

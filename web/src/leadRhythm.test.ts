import { describe, expect, it } from "vitest";
import { hasLeadRhythm, splitNotice, visibleStemIds } from "./leadRhythm";

describe("visibleStemIds", () => {
  const ids = ["vocals", "guitar", "lead_guitar", "rhythm_guitar"];

  it("shows Lead + Rhythm instead of Guitar by default", () => {
    expect(visibleStemIds(ids)).toEqual(["vocals", "lead_guitar", "rhythm_guitar"]);
  });

  it("shows the single Guitar in combined view", () => {
    expect(visibleStemIds(ids, "combined")).toEqual(["vocals", "guitar"]);
  });

  it("leaves songs without a split alone", () => {
    expect(visibleStemIds(["vocals", "guitar"])).toEqual(["vocals", "guitar"]);
    expect(hasLeadRhythm(["guitar", "lead_guitar"])).toBe(false);
  });
});

describe("splitNotice", () => {
  it("returns null when no split was tried", () => {
    expect(splitNotice(null)).toBeNull();
  });

  it("uses the engine's own message", () => {
    const n = splitNotice({ outcome: "lead_rhythm", reason_code: "split", user_message: "Split by when each part plays." });
    expect(n).toEqual({ level: "success", text: "Split by when each part plays.", split: true });
  });

  it("flags a split with uncertain labels as a best guess", () => {
    const n = splitNotice({ outcome: "lead_rhythm", reason_code: "split_labels_unsure" });
    expect(n?.split).toBe(true);
    expect(n?.level).toBe("warning");
    expect(n?.text).toContain("best guess");
  });

  it("maps older results without a reason code", () => {
    expect(splitNotice({ outcome: "ambiguous", method: "midside" })?.text).toContain("one Guitar track");
    expect(splitNotice({ outcome: "lead_rhythm", method: "register", forced_emit: true })?.level).toBe("warning");
  });
});

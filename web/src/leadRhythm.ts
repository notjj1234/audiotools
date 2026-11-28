/**
 * Lead / Rhythm guitar split helpers for the website mixer.
 * Same rules as the desktop app (ui/isolate_state.py): Lead + Rhythm add back up
 * to the Guitar stem, so the mixer shows either the pair or the single Guitar,
 * never all three (that would play the guitar twice).
 */

export const LEAD_RHYTHM_IDS = ["lead_guitar", "rhythm_guitar"] as const;

export type LeadRhythmView = "split" | "combined";

export function hasLeadRhythm(ids: readonly string[]): boolean {
  return LEAD_RHYTHM_IDS.every((id) => ids.includes(id));
}

export function visibleStemIds(ids: readonly string[], view: LeadRhythmView = "split"): string[] {
  if (!hasLeadRhythm(ids)) return [...ids];
  if (view === "combined" && ids.includes("guitar")) {
    return ids.filter((id) => !(LEAD_RHYTHM_IDS as readonly string[]).includes(id));
  }
  return ids.filter((id) => id !== "guitar");
}

export interface SplitNotice {
  level: "success" | "warning" | "info";
  text: string;
  split: boolean;
}

const FALLBACK_TEXT: Record<string, string> = {
  missing: "No guitar track was made for this song, so there was nothing to split.",
  not_present: "The guitar track is almost silent, so it was kept as one Guitar track.",
  too_short: "The guitar part is too short to tell lead from rhythm, so it was kept as one Guitar track.",
  one_part: "Only one guitar part was found, so it was kept as one Guitar track.",
  overlap:
    "The guitar parts play together in the same place in the mix, so they couldn't be pulled apart cleanly. Kept as one Guitar track.",
  unclear_roles:
    "Two guitar parts were found, but it wasn't clear which one is the lead, so they were kept together as one Guitar track.",
  split: "Split into Lead and Rhythm.",
  split_low_confidence: "Split into Lead and Rhythm as a best guess; the labels may be wrong.",
  split_labels_unsure:
    "Two guitar parts were found and split. It wasn't certain which one is the lead, so the labels are a best guess.",
};

const SPLIT_CODES = new Set(["split", "split_low_confidence", "split_labels_unsure"]);

/** Plain message from guitar_split_diagnostics.json (null when nothing was tried). */
export function splitNotice(diag: Record<string, unknown> | null | undefined): SplitNotice | null {
  if (!diag || typeof diag !== "object") return null;
  const outcome = String(diag.outcome ?? "");
  const method = String(diag.method ?? "none");
  const forced = Boolean(diag.forced_emit) || Boolean(diag.low_confidence);
  let code = String(diag.reason_code ?? "");
  if (!code) {
    if (outcome === "lead_rhythm") code = forced ? "split_low_confidence" : "split";
    else if (outcome === "skipped") code = "missing";
    else if (method === "spatial" || method === "midside") code = "overlap";
    else code = "one_part";
  }
  const text = String(diag.user_message ?? "") || FALLBACK_TEXT[code] || FALLBACK_TEXT.one_part;
  const split = SPLIT_CODES.has(code);
  const unsure = code === "split_low_confidence" || code === "split_labels_unsure";
  const level = unsure ? "warning" : split ? "success" : "info";
  return { level, text, split };
}

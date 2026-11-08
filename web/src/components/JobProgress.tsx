import type { JobResponse, JobStatus } from "../api";
import { useHeldVisible } from "../pending";

const STATUS_LABELS: Record<JobStatus, string> = {
  pending: "Pending",
  running: "Running",
  succeeded: "Succeeded",
  failed: "Failed",
  cancelled: "Cancelled",
};

function humanizeStage(stage: string): string {
  if (!stage) return "";
  const words = stage.replace(/[_-]+/g, " ").trim().split(/\s+/);
  return words
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/** 0–1 when the payload includes a finite percent. Values above 1 are 0–100. */
export function progressFraction(percent: number | null | undefined): number | null {
  if (typeof percent !== "number" || !Number.isFinite(percent)) return null;
  const unit = percent > 1 ? percent / 100 : percent;
  if (unit < 0) return 0;
  if (unit > 1) return 1;
  return unit;
}

export function JobProgress({
  job,
  onCancel,
}: {
  job: JobResponse | null;
  onCancel?: () => void;
}) {
  const done = !job || ["succeeded", "failed", "cancelled"].includes(job.status);
  const showSpinner = useHeldVisible(Boolean(job) && !done);
  if (!job) return null;
  const fraction = progressFraction(job.percent);
  const scale = fraction ?? (job.status === "succeeded" ? 1 : null);
  const percentLabel =
    fraction == null ? undefined : `${Math.round(fraction * 100)} percent`;
  return (
    <div className="progress reveal" aria-busy={!done || undefined}>
      <div className="progress-head">
        <div className="stage" aria-live="polite">
          {STATUS_LABELS[job.status] ?? job.status}
          {job.stage ? ` · ${humanizeStage(job.stage)}` : ""}
        </div>
        <span className={`spinner${showSpinner ? " is-on" : ""}`} aria-hidden="true" />
      </div>
      <p className="progress-message">{job.message || "\u00a0"}</p>
      <div
        className="progress-track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={fraction == null ? undefined : Math.round(fraction * 100)}
        aria-valuetext={done ? STATUS_LABELS[job.status] : percentLabel ?? "Working"}
      >
        <span
          className={`progress-fill${scale == null && !done ? " is-indeterminate" : ""}`}
          style={scale == null ? undefined : { transform: `scaleX(${scale})` }}
        />
      </div>
      {job.error && <p className="error fade-in">{job.error}</p>}
      {!done && onCancel && (
        <button type="button" className="danger" onClick={onCancel}>
          Cancel
        </button>
      )}
    </div>
  );
}

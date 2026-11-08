import { useEffect, useRef, useState, type ReactNode, type Ref } from "react";

/** Show a cue only after `delayMs`, then keep it up for at least `minMs`. */
export function useHeldVisible(active: boolean, delayMs = 200, minMs = 500): boolean {
  const [shown, setShown] = useState(false);
  const shownAt = useRef<number | null>(null);

  useEffect(() => {
    let timer = 0;
    if (active) {
      timer = window.setTimeout(() => {
        shownAt.current = Date.now();
        setShown(true);
      }, delayMs);
      return () => window.clearTimeout(timer);
    }

    const start = shownAt.current;
    if (start == null) {
      setShown(false);
      return;
    }
    const remaining = Math.max(0, minMs - (Date.now() - start));
    timer = window.setTimeout(() => {
      shownAt.current = null;
      setShown(false);
    }, remaining);
    return () => window.clearTimeout(timer);
  }, [active, delayMs, minMs]);

  return shown;
}

/** Stack every label in one cell so the button width stays on the widest one. */
export function StableLabel({
  value,
  options,
  pending,
}: {
  value: string;
  options: readonly string[];
  pending: boolean;
}) {
  const spinner = useHeldVisible(pending);
  return (
    <span className="btn-swap">
      {options.map((label) => {
        const on = label === value;
        return (
          <span key={label} className={on ? undefined : "is-off"}>
            <span className={`spinner${on && spinner ? " is-on" : ""}`} aria-hidden="true" />
            {label}
          </span>
        );
      })}
    </span>
  );
}

export function Fold({
  open,
  children,
}: {
  open: boolean;
  children: ReactNode;
}) {
  const ref: Ref<HTMLDivElement> = (node) => {
    if (!node) return;
    if (open) node.removeAttribute("inert");
    else node.setAttribute("inert", "");
  };
  return (
    <div
      className={`fold${open ? " is-open" : ""}`}
      ref={ref}
    >
      <div className="fold-inner">{children}</div>
    </div>
  );
}

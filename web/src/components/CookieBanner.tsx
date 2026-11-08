import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { COOKIE_ACK_KEY } from "../legal/placeholders";

function bannerVisible(): boolean {
  try {
    return localStorage.getItem(COOKIE_ACK_KEY) !== "1";
  } catch {
    return true;
  }
}

export function CookieBanner() {
  const [visible, setVisible] = useState(bannerVisible);
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    if (!leaving) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const id = window.setTimeout(() => setVisible(false), reduce ? 80 : 160);
    return () => window.clearTimeout(id);
  }, [leaving]);

  if (!visible) return null;

  function acknowledge() {
    try {
      localStorage.setItem(COOKIE_ACK_KEY, "1");
    } catch {
      /* private mode */
    }
    setLeaving(true);
  }

  return (
    <div
      className={`cookie-banner${leaving ? " is-leaving" : ""}`}
      role="dialog"
      aria-label="Cookie notice"
    >
      <p>
        We use an <strong>essential</strong> HttpOnly refresh cookie (
        <code>att_refresh</code>) for sign-in, plus a short-lived access token in{" "}
        <code>sessionStorage</code>. No advertising cookies in this demo.{" "}
        <Link to="/legal/cookies">Cookie policy</Link>
      </p>
      <button type="button" onClick={acknowledge}>
        OK
      </button>
    </div>
  );
}

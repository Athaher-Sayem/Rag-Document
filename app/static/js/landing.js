/* landing.js — hero citation-trace viz, live count-up metrics, demo chat. */
(function () {
  "use strict";

  const reduceMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  /* ---------- Hero visualization timeline ---------- */
  function runViz() {
    const svg = document.querySelector(".hero-viz svg");
    if (!svg) return;
    const chunks = Array.from(svg.querySelectorAll(".chunk"));
    const links = Array.from(svg.querySelectorAll(".link"));
    const lines = Array.from(svg.querySelectorAll(".ans-line"));
    const chips = Array.from(svg.querySelectorAll(".ans-chip"));
    const glow = [1, 5, 9]; // one chunk per page

    const setTransitions = (el, prop) => {
      el.style.transition = prop;
    };
    chunks.forEach((c) => setTransitions(c, "fill 0.3s ease"));
    links.forEach((l) => setTransitions(l, "stroke-dashoffset 0.45s ease"));
    lines.forEach((l) => setTransitions(l, "opacity 0.3s ease"));
    chips.forEach((c) => setTransitions(c, "opacity 0.3s ease"));

    const reset = () => {
      chunks.forEach((c) => (c.style.fill = "#DCE3D3"));
      links.forEach((l) => (l.style.strokeDashoffset = l.getAttribute("stroke-dasharray")));
      lines.forEach((l) => (l.style.opacity = 0));
      chips.forEach((c) => (c.style.opacity = 0));
    };

    const play = () => {
      reset();
      if (reduceMotion) return finish();

      glow.forEach((idx, n) =>
        setTimeout(() => {
          if (chunks[idx]) chunks[idx].style.fill = "#2F7A57";
        }, 350 + n * 220)
      );
      setTimeout(() => links.forEach((l) => (l.style.strokeDashoffset = 0)), 1200);
      lines.forEach((l, n) =>
        setTimeout(() => (l.style.opacity = 1), 1550 + n * 180)
      );
      setTimeout(() => chips.forEach((c) => (c.style.opacity = 1)), 2100);
    };

    const finish = () => {
      glow.forEach((idx) => {
        if (chunks[idx]) chunks[idx].style.fill = "#2F7A57";
      });
      links.forEach((l) => (l.style.strokeDashoffset = 0));
      lines.forEach((l) => (l.style.opacity = 1));
      chips.forEach((c) => (c.style.opacity = 1));
    };

    svg.addEventListener("click", play);
    play();
    if (!reduceMotion) {
      setInterval(play, 5200);
    }
  }

  /* ---------- Count-up metrics ---------- */
  function easeOut(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function countUp(el, target) {
    const isFloat = !Number.isInteger(target);
    const duration = reduceMotion ? 0 : 900;
    const start = performance.now();
    function frame(now) {
      const p = duration === 0 ? 1 : Math.min((now - start) / duration, 1);
      const value = target * easeOut(p);
      el.textContent = isFloat ? value.toFixed(1) : Math.round(value).toLocaleString();
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  function loadStats() {
    fetch("/api/stats")
      .then((r) => r.json())
      .then((s) => {
        const map = {
          chunks: s.total_chunks,
          pages: s.total_pages,
          documents: s.documents,
          avg: s.avg_chunks_per_doc,
        };
        document.querySelectorAll(".metric-value").forEach((el) => {
          const key = el.getAttribute("data-count");
          if (map[key] != null) countUp(el, map[key]);
        });
        const c = document.getElementById("hero-chunks");
        const d = document.getElementById("hero-docs");
        if (c) c.textContent = (s.total_chunks || 0).toLocaleString();
        if (d) d.textContent = s.documents || 0;
      })
      .catch(() => {});
  }

  /* ---------- Demo chat (SSE) ---------- */
  function streamChat(sessionId, message, onToken, onCitations) {
    return fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    }).then((res) => {
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      function pump() {
        return reader.read().then(({ value, done }) => {
          if (done) return;
          buffer += decoder.decode(value, { stream: true });
          let idx;
          while ((idx = buffer.indexOf("\n\n")) !== -1) {
            const raw = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);
            const line = raw.startsWith("data: ") ? raw.slice(6) : raw;
            if (!line.trim()) continue;
            try {
              const evt = JSON.parse(line);
              if (evt.type === "token") onToken(evt.text);
              else if (evt.type === "citations") onCitations(evt.citations);
            } catch (e) {
              /* ignore partial */
            }
          }
          return pump();
        });
      }
      return pump();
    });
  }

  function citationCard(c) {
    const el = document.createElement("div");
    el.className = "citation";
    el.innerHTML =
      '<div class="meta"><span class="chip">' +
      c.source +
      " · p." +
      c.page +
      "</span></div>" +
      '<div class="quote">' +
      escapeHtml(c.quote) +
      "</div>";
    return el;
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (m) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m])
    );
  }

  function setupDemo() {
    const form = document.getElementById("demo-form");
    const input = document.getElementById("demo-input");
    const body = document.getElementById("demo-body");
    if (!form) return;
    const sessionId = "demo-" + Math.random().toString(36).slice(2);

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const message = input.value.trim();
      if (!message) return;
      input.value = "";

      body.innerHTML = "";
      const q = document.createElement("div");
      q.className = "demo-msg user";
      q.innerHTML = '<div class="role">You</div><div class="body"></div>';
      q.querySelector(".body").textContent = message;
      body.appendChild(q);

      const a = document.createElement("div");
      a.className = "demo-msg";
      a.innerHTML = '<div class="role">Folio</div><div class="body answer"></div>';
      const answerEl = a.querySelector(".answer");
      body.appendChild(a);

      const cites = document.createElement("div");
      cites.className = "citations";
      body.appendChild(cites);

      streamChat(
        sessionId,
        message,
        (tok) => {
          answerEl.textContent += tok;
        },
        (list) => {
          cites.innerHTML = "";
          list.forEach((c) => cites.appendChild(citationCard(c)));
        }
      );
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    runViz();
    loadStats();
    setupDemo();
  });
})();

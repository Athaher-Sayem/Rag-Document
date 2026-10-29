/* chat.js — streaming chat client with citation rendering and source scoping. */
(function () {
  "use strict";

  const sessionId = "chat-" + Math.random().toString(36).slice(2);
  const stream = document.getElementById("stream");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const select = document.getElementById("doc-select");
  const citationsEl = document.getElementById("citations");
  const emptyState = document.getElementById("empty-state");

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (m) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m])
    );
  }

  function clearEmpty() {
    if (emptyState && emptyState.parentNode) emptyState.remove();
  }

  function addMessage(role, text) {
    clearEmpty();
    const el = document.createElement("div");
    el.className = "message " + (role === "user" ? "user" : "");
    el.innerHTML =
      '<div class="role">' +
      (role === "user" ? "You" : "Folio") +
      '</div><div class="bubble"></div>';
    el.querySelector(".bubble").textContent = text;
    stream.appendChild(el);
    stream.scrollTop = stream.scrollHeight;
    return el.querySelector(".bubble");
  }

  function citationCard(c) {
    const el = document.createElement("div");
    el.className = "citation";
    el.innerHTML =
      '<div class="meta"><span class="chip">' +
      escapeHtml(c.source) +
      " · p." +
      c.page +
      "</span></div>" +
      '<div class="quote">' +
      escapeHtml(c.quote) +
      "</div>";
    return el;
  }

  function streamChat(message, source, onToken, onCitations) {
    return fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message, source: source || null }),
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

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";

    addMessage("user", message);
    const bubble = addMessage("ai", "");
    citationsEl.innerHTML = "";

    streamChat(
      message,
      select.value,
      (tok) => {
        bubble.textContent += tok;
        stream.scrollTop = stream.scrollHeight;
      },
      (list) => {
        citationsEl.innerHTML = "";
        if (!list.length) {
          citationsEl.innerHTML = '<p class="empty" style="padding:0;">No citations for this answer.</p>';
          return;
        }
        list.forEach((c) => citationsEl.appendChild(citationCard(c)));
      }
    ).catch(() => {
      bubble.textContent = "Something went wrong. Check that the server is running and an API key is set.";
    });
  });

  input.focus();
})();

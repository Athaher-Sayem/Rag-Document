/* upload.js — drag-drop upload + optimistic delete with an undo window. */
(function () {
  "use strict";

  const zone = document.getElementById("upload-zone");
  const fileInput = document.getElementById("file-input");
  const tbody = document.getElementById("doc-tbody");

  function uploadFiles(files) {
    const pdfs = Array.from(files).filter((f) =>
      f.name.toLowerCase().endsWith(".pdf")
    );
    if (!pdfs.length) return;
    const form = new FormData();
    pdfs.forEach((f) => form.append("files", f));
    zone.style.opacity = "0.6";
    fetch("/api/upload", { method: "POST", body: form })
      .then((r) => r.json())
      .then(() => window.location.reload())
      .catch(() => {
        zone.style.opacity = "1";
        showToast("Upload failed. Try again.");
      });
  }

  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("drag");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag");
    uploadFiles(e.dataTransfer.files);
  });
  fileInput.addEventListener("change", () => uploadFiles(fileInput.files));

  /* ---------- Optimistic delete with undo ---------- */
  function removeRow(source) {
    const row = tbody.querySelector('tr[data-source="' + cssEscape(source) + '"]');
    if (!row) return;
    row.style.display = "none";

    let cancelled = false;
    const toast = showToast(
      "Removed " + source,
      "Undo",
      () => {
        cancelled = true;
        row.style.display = "";
        removeToast(toast);
      }
    );

    setTimeout(() => {
      removeToast(toast);
      if (cancelled) return;
      fetch("/api/documents/" + encodeURIComponent(source), { method: "DELETE" })
        .then(() => row.remove())
        .catch(() => {
          row.style.display = "";
          showToast("Could not remove " + source);
        });
    }, 5000);
  }

  tbody.addEventListener("click", (e) => {
    const btn = e.target.closest(".del");
    if (btn) removeRow(btn.getAttribute("data-source"));
  });

  /* ---------- Toast helpers ---------- */
  function showToast(message, actionLabel, onAction) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    if (actionLabel && onAction) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = actionLabel;
      btn.style.cssText =
        "background:none;border:none;color:var(--accent);font-family:var(--font-body);font-size:0.9375rem;cursor:pointer;text-decoration:underline;min-height:auto;padding:0;";
      btn.addEventListener("click", onAction);
      toast.appendChild(btn);
    }
    document.body.appendChild(toast);
    if (!actionLabel) setTimeout(() => removeToast(toast), 3000);
    return toast;
  }

  function removeToast(toast) {
    if (toast && toast.parentNode) toast.parentNode.removeChild(toast);
  }

  function cssEscape(s) {
    return s.replace(/["\\]/g, "\\$&");
  }
})();

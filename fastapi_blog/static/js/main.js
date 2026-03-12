(function () {
  const saved = localStorage.getItem("theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
}

function toggleLike(el) {
  const isLiked = el.classList.toggle("liked");
  const icon = el.querySelector(".like-icon");
  const count = el.querySelector(".like-count");
  if (!icon || !count) return;
  icon.textContent = isLiked ? "♥" : "♡";
  count.textContent = isLiked
    ? parseInt(count.textContent) + 1
    : Math.max(0, parseInt(count.textContent) - 1);
}

function showToast(message, type = "success") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${type === "success" ? "✓" : "✕"}</span>
    <span class="toast-msg">${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
  `;
  container.appendChild(toast);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => toast.classList.add("toast-visible"));
  });

  setTimeout(() => {
    toast.classList.remove("toast-visible");
    setTimeout(() => toast.remove(), 350);
  }, 4000);
}

function showConfirm(message, onConfirm) {
  const existing = document.getElementById("confirm-modal");
  if (existing) existing.remove();

  const modal = document.createElement("div");
  modal.id = "confirm-modal";
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-icon">🗑</div>
      <p class="modal-message">${message}</p>
      <div class="modal-actions">
        <button class="modal-btn modal-btn-cancel" id="modal-cancel">Cancel</button>
        <button class="modal-btn modal-btn-danger" id="modal-confirm">Delete</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => modal.classList.add("modal-visible"));
  });

  const close = () => {
    modal.classList.remove("modal-visible");
    setTimeout(() => modal.remove(), 200);
  };

  document.getElementById("modal-cancel").onclick = close;
  document.getElementById("modal-confirm").onclick = () => {
    close();
    onConfirm();
  };
  modal.addEventListener("click", (e) => {
    if (e.target === modal) close();
  });
}

function showFieldError(fieldId, message) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  field.classList.add("field-error");
  let hint = field.parentElement.querySelector(".field-hint");
  if (!hint) {
    hint = document.createElement("span");
    hint.className = "field-hint";
    field.after(hint);
  }
  hint.textContent = message;
}

function clearFieldErrors() {
  document
    .querySelectorAll(".field-error")
    .forEach((el) => el.classList.remove("field-error"));
  document.querySelectorAll(".field-hint").forEach((el) => el.remove());
}

function showFormError(message) {
  const el = document.getElementById("form-error");
  if (!el) return;
  el.textContent = message;
  el.style.display = "block";
  el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function clearFormError() {
  const el = document.getElementById("form-error");
  if (el) el.style.display = "none";
}

function setButtonLoading(btn, text) {
  btn.disabled = true;
  const span = btn.querySelector(".btn-text");
  if (span) span.textContent = text;
}

function resetButton(btn, text) {
  btn.disabled = false;
  const span = btn.querySelector(".btn-text");
  if (span) span.textContent = text;
}

async function submitPost() {
  clearFieldErrors();
  clearFormError();

  const title = document.getElementById("title")?.value.trim();
  const content = document.getElementById("content")?.value.trim();

  let valid = true;

  if (!title) {
    showFieldError("title", "Title is required");
    valid = false;
  } else if (title.length > 100) {
    showFieldError("title", `Too long — ${title.length}/100 characters`);
    valid = false;
  }
  if (!content) {
    showFieldError("content", "Content is required");
    valid = false;
  }

  if (!valid) return;

  const btn = document.querySelector(".btn-submit");
  setButtonLoading(btn, "Publishing…");

  try {
    const res = await fetch("/api/posts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    });

    if (!res.ok) {
      const data = await res.json();
      _handleApiErrors(data.detail);
      resetButton(btn, "Publish Post");
      return;
    }

    const post = await res.json();
    showToast("Post published!", "success");
    window.location.href = `/posts/${post.id}`;
  } catch {
    showFormError("Network error. Please try again.");
    resetButton(btn, "Publish Post");
  }
}

async function updatePost(postId) {
  clearFieldErrors();
  clearFormError();

  const title = document.getElementById("title")?.value.trim();
  const content = document.getElementById("content")?.value.trim();

  let valid = true;

  if (!title) {
    showFieldError("title", "Title is required");
    valid = false;
  } else if (title.length > 100) {
    showFieldError("title", `Too long — ${title.length}/100 characters`);
    valid = false;
  }
  if (!content) {
    showFieldError("content", "Content is required");
    valid = false;
  }

  if (!valid) return;

  const btn = document.querySelector(".btn-submit");
  setButtonLoading(btn, "Saving…");

  try {
    const res = await fetch(`/api/posts/${postId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    });

    if (!res.ok) {
      const data = await res.json();
      _handleApiErrors(data.detail);
      resetButton(btn, "Save Changes");
      return;
    }

    showToast("Post updated!", "success");
    window.location.href = `/posts/${postId}`;
  } catch {
    showFormError("Network error. Please try again.");
    resetButton(btn, "Save Changes");
  }
}

function deletePost(postId) {
  showConfirm("Delete this post? This action cannot be undone.", async () => {
    try {
      const res = await fetch(`/api/posts/${postId}`, { method: "DELETE" });
      if (res.ok || res.status === 204) {
        showToast("Post deleted.", "success");
        setTimeout(() => (window.location.href = "/posts"), 900);
      } else {
        const data = await res.json().catch(() => ({}));
        showToast(data.detail || "Failed to delete post.", "error");
      }
    } catch {
      showToast("Network error. Please try again.", "error");
    }
  });
}

function _handleApiErrors(detail) {
  if (Array.isArray(detail)) {
    detail.forEach((err) => {
      const loc = err.loc?.[err.loc.length - 1];
      if (loc && loc !== "body") {
        showFieldError(String(loc), err.msg);
      } else {
        showFormError(err.msg);
      }
    });
  } else {
    showFormError(detail || "Something went wrong.");
  }
}

function initCharCounter(inputId, counterId, max) {
  const input = document.getElementById(inputId);
  const counter = document.getElementById(counterId);
  if (!input || !counter) return;

  const update = () => {
    const len = input.value.length;
    counter.textContent = `${len} / ${max}`;
    counter.classList.toggle("counter-warn", len > max * 0.85);
    counter.classList.toggle("counter-over", len >= max);
  };

  input.addEventListener("input", update);
  update();
}

document.addEventListener("DOMContentLoaded", () => {
  initCharCounter("title", "title-counter", 100);
});



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

  requestAnimationFrame(() =>
    requestAnimationFrame(() => toast.classList.add("toast-visible")),
  );

  setTimeout(() => {
    toast.classList.remove("toast-visible");
    setTimeout(() => toast.remove(), 350);
  }, 4000);
}


function showConfirm(
  message,
  onConfirm,
  { icon = "🗑", confirmLabel = "Delete", danger = true } = {},
) {
  const existing = document.getElementById("confirm-modal");
  if (existing) existing.remove();

  const modal = document.createElement("div");
  modal.id = "confirm-modal";
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-icon">${icon}</div>
      <p class="modal-message">${message}</p>
      <div class="modal-actions">
        <button class="modal-btn modal-btn-cancel" id="modal-cancel">Cancel</button>
        <button class="modal-btn ${danger ? "modal-btn-danger" : "modal-btn-primary"}" id="modal-confirm">
          ${confirmLabel}
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  requestAnimationFrame(() =>
    requestAnimationFrame(() => modal.classList.add("modal-visible")),
  );

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

function clearFieldErrors(formEl) {
  const root = formEl || document;
  root
    .querySelectorAll(".field-error")
    .forEach((el) => el.classList.remove("field-error"));
  root.querySelectorAll(".field-hint").forEach((el) => el.remove());
}

function showFormError(elId, message) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.textContent = message;
  el.style.display = "block";
  el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function clearFormError(elId) {
  const el = document.getElementById(elId);
  if (el) el.style.display = "none";
}

function setBtnLoading(btn, text) {
  btn.disabled = true;
  const span = btn.querySelector(".btn-text");
  if (span) span.textContent = text;
}

function resetBtn(btn, text) {
  btn.disabled = false;
  const span = btn.querySelector(".btn-text");
  if (span) span.textContent = text;
}

/** Обработать ошибки из API (может быть строка или массив Pydantic-ошибок) */
function handleApiErrors(detail, formErrorId = "form-error") {
  if (Array.isArray(detail)) {
    detail.forEach((err) => {
      const loc = err.loc?.[err.loc.length - 1];
      if (loc && loc !== "body") showFieldError(String(loc), err.msg);
      else showFormError(formErrorId, err.msg);
    });
  } else {
    showFormError(formErrorId, detail || "Something went wrong.");
  }
}


async function register() {
  clearFieldErrors();
  clearFormError("form-error");

  const username = document.getElementById("username")?.value.trim();
  const email = document.getElementById("email")?.value.trim();
  const password = document.getElementById("password")?.value;
  const confirm = document.getElementById("password_confirm")?.value;

  let valid = true;

  if (!username) {
    showFieldError("username", "Username is required");
    valid = false;
  } else if (username.length > 50) {
    showFieldError("username", "Max 50 characters");
    valid = false;
  }

  if (!email) {
    showFieldError("email", "Email is required");
    valid = false;
  }

  if (!password) {
    showFieldError("password", "Password is required");
    valid = false;
  } else if (password.length < 8) {
    showFieldError("password", "Minimum 8 characters");
    valid = false;
  }

  if (password && confirm !== undefined && confirm !== password) {
    showFieldError("password_confirm", "Passwords do not match");
    valid = false;
  }

  if (!valid) return;

  const btn = document.querySelector(".btn-submit");
  setBtnLoading(btn, "Creating account…");

  try {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });

    if (!res.ok) {
      const data = await res.json();
      handleApiErrors(data.detail);
      resetBtn(btn, "Create Account");
      return;
    }

    await _performLogin(username, password);
  } catch {
    showFormError("form-error", "Network error. Please try again.");
    resetBtn(btn, "Create Account");
  }
}

async function login() {
  clearFieldErrors();
  clearFormError("form-error");

  const username = document.getElementById("username")?.value.trim();
  const password = document.getElementById("password")?.value;

  let valid = true;
  if (!username) {
    showFieldError("username", "Username or email is required");
    valid = false;
  }
  if (!password) {
    showFieldError("password", "Password is required");
    valid = false;
  }
  if (!valid) return;

  const btn = document.querySelector(".btn-submit");
  setBtnLoading(btn, "Logging in…");

  try {
    await _performLogin(username, password);
  } catch {
    showFormError("form-error", "Network error. Please try again.");
    resetBtn(btn, "Log In");
  }
}

async function _performLogin(username, password) {
  const btn = document.querySelector(".btn-submit");
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const data = await res.json();
    handleApiErrors(data.detail);
    resetBtn(btn, btn?.querySelector(".btn-text")?.textContent || "Submit");
    return;
  }

  const next = new URLSearchParams(window.location.search).get("next") || "/";
  window.location.href = next;
}

async function logout() {
  await fetch("/api/auth/logout", { method: "POST" });
  window.location.href = "/";
}


async function submitPost() {
  clearFieldErrors();
  clearFormError("form-error");

  const title = document.getElementById("title")?.value.trim();
  const content = document.getElementById("content")?.value.trim();

  let valid = true;
  if (!title) {
    showFieldError("title", "Title is required");
    valid = false;
  } else if (title.length > 100) {
    showFieldError("title", `Too long — ${title.length}/100`);
    valid = false;
  }
  if (!content) {
    showFieldError("content", "Content is required");
    valid = false;
  }
  if (!valid) return;

  const btn = document.querySelector(".btn-submit");
  setBtnLoading(btn, "Publishing…");

  try {
    const res = await fetch("/api/posts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    });

    if (res.status === 401) {
      window.location.href = "/login?next=/posts/create";
      return;
    }

    if (!res.ok) {
      const data = await res.json();
      handleApiErrors(data.detail);
      resetBtn(btn, "Publish Post");
      return;
    }

    const post = await res.json();
    showToast("Post published!", "success");
    window.location.href = `/posts/${post.id}`;
  } catch {
    showFormError("form-error", "Network error. Please try again.");
    resetBtn(btn, "Publish Post");
  }
}

async function updatePost(postId) {
  clearFieldErrors();
  clearFormError("form-error");

  const title = document.getElementById("title")?.value.trim();
  const content = document.getElementById("content")?.value.trim();

  let valid = true;
  if (!title) {
    showFieldError("title", "Title is required");
    valid = false;
  } else if (title.length > 100) {
    showFieldError("title", `Too long — ${title.length}/100`);
    valid = false;
  }
  if (!content) {
    showFieldError("content", "Content is required");
    valid = false;
  }
  if (!valid) return;

  const btn = document.querySelector(".btn-submit");
  setBtnLoading(btn, "Saving…");

  try {
    const res = await fetch(`/api/posts/${postId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    });

    if (!res.ok) {
      const data = await res.json();
      handleApiErrors(data.detail);
      resetBtn(btn, "Save Changes");
      return;
    }

    showToast("Post updated!", "success");
    window.location.href = `/posts/${postId}`;
  } catch {
    showFormError("form-error", "Network error. Please try again.");
    resetBtn(btn, "Save Changes");
  }
}

function deletePost(postId) {
  showConfirm("Delete this post? This cannot be undone.", async () => {
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
      showToast("Network error.", "error");
    }
  });
}


async function updateProfile() {
  const form = document.getElementById("profile-form");
  clearFieldErrors(form);
  clearFormError("profile-error");

  const username = document.getElementById("username")?.value.trim();
  const email = document.getElementById("email")?.value.trim();

  let valid = true;
  if (!username) {
    showFieldError("username", "Username is required");
    valid = false;
  }
  if (!email) {
    showFieldError("email", "Email is required");
    valid = false;
  }
  if (!valid) return;

  const btn = document.getElementById("profile-btn");
  setBtnLoading(btn, "Saving…");

  try {
    const res = await fetch("/api/users/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email }),
    });

    if (!res.ok) {
      const data = await res.json();
      handleApiErrors(data.detail, "profile-error");
      resetBtn(btn, "Save Changes");
      return;
    }

    showToast("Profile updated!", "success");
    resetBtn(btn, "Save Changes");
  } catch {
    showFormError("profile-error", "Network error.");
    resetBtn(btn, "Save Changes");
  }
}

async function changePassword() {
  const form = document.getElementById("password-form");
  clearFieldErrors(form);
  clearFormError("password-error");

  const currentPwd = document.getElementById("current_password")?.value;
  const newPwd = document.getElementById("new_password")?.value;
  const confirmPwd = document.getElementById("confirm_password")?.value;

  let valid = true;
  if (!currentPwd) {
    showFieldError("current_password", "Current password is required");
    valid = false;
  }
  if (!newPwd) {
    showFieldError("new_password", "New password is required");
    valid = false;
  } else if (newPwd.length < 8) {
    showFieldError("new_password", "Minimum 8 characters");
    valid = false;
  }
  if (newPwd && confirmPwd !== newPwd) {
    showFieldError("confirm_password", "Passwords do not match");
    valid = false;
  }
  if (!valid) return;

  const btn = document.getElementById("password-btn");
  setBtnLoading(btn, "Saving…");

  try {
    const res = await fetch("/api/users/me/password", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        current_password: currentPwd,
        new_password: newPwd,
      }),
    });

    if (!res.ok) {
      const data = await res.json();
      handleApiErrors(data.detail, "password-error");
      resetBtn(btn, "Change Password");
      return;
    }

    showToast("Password changed!", "success");
    document.getElementById("current_password").value = "";
    document.getElementById("new_password").value = "";
    document.getElementById("confirm_password").value = "";
    resetBtn(btn, "Change Password");
  } catch {
    showFormError("password-error", "Network error.");
    resetBtn(btn, "Change Password");
  }
}

function deleteAccount() {
  showConfirm(
    "Permanently delete your account and all posts? This cannot be undone.",
    async () => {
      try {
        const res = await fetch("/api/users/me", { method: "DELETE" });
        if (res.ok || res.status === 204) {
          showToast("Account deleted.", "success");
          setTimeout(() => (window.location.href = "/"), 1000);
        } else {
          const data = await res.json().catch(() => ({}));
          showToast(data.detail || "Failed to delete account.", "error");
        }
      } catch {
        showToast("Network error.", "error");
      }
    },
    { icon: "⚠️", confirmLabel: "Delete Account" },
  );
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

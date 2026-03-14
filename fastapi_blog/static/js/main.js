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

async function submitPost() {
  const author = document.getElementById("author")?.value.trim();
  const title = document.getElementById("title")?.value.trim();
  const content = document.getElementById("content")?.value.trim();
  const userId = document.getElementById("user_id")?.value.trim();
  const errorEl = document.getElementById("form-error");

  if (!title || !content || !userId) {
    errorEl.textContent = "Please fill in all fields.";
    errorEl.style.display = "block";
    return;
  }

  errorEl.style.display = "none";
  const btn = document.querySelector(".btn-submit");
  btn.disabled = true;
  btn.querySelector(".btn-text").textContent = "Publishing...";

  try {
    const response = await fetch("/api/posts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content, user_id: parseInt(userId) }),
    });

    if (!response.ok) {
      const data = await response.json();
      errorEl.textContent = data.detail || "Something went wrong.";
      errorEl.style.display = "block";
      btn.disabled = false;
      btn.querySelector(".btn-text").textContent = "Publish Post";
      return;
    }

    const post = await response.json();
    window.location.href = `/posts/${post.id}`;
  } catch (err) {
    errorEl.textContent = "Network error. Please try again.";
    errorEl.style.display = "block";
    btn.disabled = false;
    btn.querySelector(".btn-text").textContent = "Publish Post";
  }
}

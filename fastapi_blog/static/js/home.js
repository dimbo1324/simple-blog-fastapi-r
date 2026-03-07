function toggleLike(el) {
  const isLiked = el.classList.toggle("liked");
  const icon = el.querySelector(".like-icon");
  const count = el.querySelector(".like-count");
  icon.textContent = isLiked ? "♥" : "♡";
  count.textContent = isLiked
    ? parseInt(count.textContent) + 1
    : Math.max(0, parseInt(count.textContent) - 1);
}

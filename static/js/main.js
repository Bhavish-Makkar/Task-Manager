document.addEventListener("DOMContentLoaded", () => {
    const commentForm = document.querySelector("[data-comment-submit]")?.form;
    const submitButton = document.querySelector("[data-comment-submit]");
    const body = commentForm?.querySelector("textarea");
    if (!commentForm || !submitButton || !body) return;
    const updateButton = () => { submitButton.disabled = !body.value.trim(); };
    body.addEventListener("input", updateButton);
    updateButton();
});

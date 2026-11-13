"use strict";

/* Dismiss toasts: close buttons, and success or info toasts after 6 seconds. */
(() => {
    const stack = document.querySelector("[data-toast-stack]");
    if (!stack) return;

    function dismiss(toast) {
        toast.classList.add("is-leaving");
        window.setTimeout(() => toast.remove(), 200);
    }

    stack.addEventListener("click", (event) => {
        const button = event.target.closest("[data-toast-close]");
        if (button) dismiss(button.closest(".toast"));
    });

    stack.querySelectorAll("[data-toast-autohide]").forEach((toast) => {
        let timer = window.setTimeout(() => dismiss(toast), 6000);
        // Keep the toast while the pointer or keyboard focus is on it.
        toast.addEventListener("mouseenter", () => window.clearTimeout(timer));
        toast.addEventListener("focusin", () => window.clearTimeout(timer));
        toast.addEventListener("mouseleave", () => {
            timer = window.setTimeout(() => dismiss(toast), 3000);
        });
    });
})();

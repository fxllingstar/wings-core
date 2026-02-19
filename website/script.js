// ===== GSAP INTRO ANIMATION =====
gsap.from(".landingpageh1 h1", {
    y: 100,
    opacity: 0,
    duration: 1.5,
    ease: "power4.out"
});

gsap.from(".landing-page h3", {
    y: 50,
    opacity: 0,
    delay: 0.5,
    duration: 1.2
});

// ===== SCROLL ANIMATION =====
gsap.from(".functionality-page", {
    scrollTrigger: {
        trigger: ".functionality-page",
        start: "top 80%",
    },
    y: 100,
    opacity: 0,
    duration: 1.5
});

// ===== SECRET FOOTER EASTER EGG =====
document.querySelector(".footer").addEventListener("click", () => {
    Swal.fire({
        title: "You found it.",
        text: "Run: wings-core qotd",
        background: "#111",
        color: "#fff",
        confirmButtonColor: "#00c3ff"
    });
});

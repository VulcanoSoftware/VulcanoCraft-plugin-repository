// Functie om AOS te initialiseren
function initAOS() {
    AOS.init({
        duration: 1000,
        easing: "ease-in-out",
        once: false,
        mirror: true,
        offset: 100,
    });
}

// Functie om GSAP-animaties te initialiseren
function initGSAPAnimations() {
    // Animeer de header
    gsap.from(".navbar", {
        y: -100,
        opacity: 0,
        duration: 1.2,
        ease: "power3.out",
    });

    // Animeer de floating add button
    gsap.to(".floating-add-btn", {
        y: -10,
        duration: 1.5,
        repeat: -1,
        yoyo: true,
        ease: "power1.inOut",
    });

    // Staggered animatie voor badges
    gsap.from(".version-badge", {
        scale: 0,
        opacity: 0,
        stagger: 0.1,
        duration: 0.5,
        ease: "back.out(1.7)",
        scrollTrigger: {
            trigger: ".versions-container",
            start: "top bottom-=100",
            toggleActions: "play none none none",
        },
    });
}

// Functie om interactieve animaties te initialiseren
function initInteractiveAnimations() {
    // Plugin iconen animatie bij hover
    const pluginIcons = document.querySelectorAll(".plugin-icon");
    pluginIcons.forEach((icon) => {
        icon.addEventListener("mouseover", function () {
            gsap.to(this, {
                rotation: 10,
                scale: 1.15,
                duration: 0.3,
                ease: "power2.out",
            });
        });

        icon.addEventListener("mouseout", function () {
            gsap.to(this, {
                rotation: 0,
                scale: 1,
                duration: 0.3,
                ease: "power2.out",
            });
        });
    });

    // Animatie voor knoppen
    const buttons = document.querySelectorAll(".btn");
    buttons.forEach((btn) => {
        btn.addEventListener("mouseover", function () {
            gsap.to(this, {
                scale: 1.03,
                duration: 0.3,
                ease: "power2.out",
            });
        });

        btn.addEventListener("mouseout", function () {
            gsap.to(this, {
                scale: 1,
                duration: 0.28,
                ease: "power2.inOut",
            });
        });

        btn.addEventListener("mousedown", function () {
            gsap.to(this, {
                scale: 0.97,
                duration: 0.12,
                ease: "power2.out",
            });
        });

        btn.addEventListener("mouseup", function () {
            gsap.to(this, {
                scale: 1.03,
                duration: 0.16,
                ease: "power2.out",
            });
        });
    });

    // Animatie voor kaarten bij verschijnen
    const cards = document.querySelectorAll(".card");
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });

    // Animatie voor floating elementen bij klikken
    const floatingElements = document.querySelectorAll(".floating-element");
    floatingElements.forEach((element) => {
        element.addEventListener("click", function () {
            gsap.to(this, {
                scale: 1.2,
                rotation: "+=20",
                duration: 0.5,
                ease: "elastic.out(1, 0.3)",
            });

            setTimeout(() => {
                gsap.to(this, {
                    scale: 1,
                    rotation: "-=20",
                    duration: 1,
                    ease: "elastic.out(1, 0.3)",
                });
            }, 500);
        });
    });
}

// Functie om Anime.js-animaties te initialiseren
function initAnimeJS() {
    // Wrap every letter in a span
    var textWrapper = document.querySelector(".ml9 .letters");
    textWrapper.innerHTML = textWrapper.textContent.replace(
        /\S/g,
        "<span class='letter'>$&</span>"
    );

    anime
        .timeline({ loop: true })
        .add({
            targets: ".ml9 .letter",
            scale: [0, 1],
            duration: 1500,
            elasticity: 600,
            delay: (el, i) => 45 * (i + 1),
        })
        .add({
            targets: ".ml9",
            opacity: 1,
            duration: 1000,
            easing: "easeOutExpo",
            delay: 1000,
        });

    //add-plugin animation
    const button = document.querySelector(".button-creative");
    const glow = button.querySelector("::before");

    button.addEventListener("mousemove", (e) => {
        const rect = button.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        button.style.setProperty("--x", `${x}px`);
        button.style.setProperty("--y", `${y}px`);
    });
}

// Exporteer de initialisatiefuncties
export function initializeAnimations() {
    document.addEventListener("DOMContentLoaded", function () {
        initAOS();
        initGSAPAnimations();
        initInteractiveAnimations();
        initAnimeJS();
    });
}

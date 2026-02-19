particlesJS("particles-js", {
    particles: {
        number: {
            value: 200
        },
        color: {
            value: "#00c3ff"
        },
        shape: {
            type: "circle"
        },
        opacity: {
            value: 0.8
        },
        size: {
            value: 3
        },
        line_linked: {
            enable: true,
            distance: 150,
            color: "#00c3ff",
            opacity: 0.5,
            width: 1
        },
        move: {
            enable: true,
            speed: 2
        }
    },
    interactivity: {
        events: {
            onhover: {
                enable: true,
                mode: "repulse"
            }
        },
        modes: {
            repulse: {
                distance: 100
            }
        }
    },
    retina_detect: true
});

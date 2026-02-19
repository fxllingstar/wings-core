//imports
import Swal from 'sweetalert2'


//GSAP ANIMATIONS
gsap.to(".landingpageh1", {x:50, duration: 0.5, repeat: -1, yoyo: true, ease: "power1.inOut"});

//GSAP Smooth Scroll
document.querySelectorAll('body').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            gsap.to(window, {scrollTo: targetElement.offsetTop, duration: 1, ease: "power2.inOut"});
        }
    });
});

//SweetAlert Test
Swal.fire({
  title: 'Error!',
  text: 'Do you want to continue',
  icon: 'error',
  confirmButtonText: 'Cool'
})

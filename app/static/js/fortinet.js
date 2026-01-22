document.querySelectorAll(".nav-item").forEach(link => {
    if (link.href === window.location.href) {
        link.style.background = "#273340";
        link.style.paddingLeft = "26px";
    }
});

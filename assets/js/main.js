(function () {
  var root = document.documentElement;
  var stored = localStorage.getItem("theme");
  var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  if (stored === "dark" || (!stored && prefersDark)) {
    root.setAttribute("data-theme", "dark");
  }

  document.addEventListener("DOMContentLoaded", function () {
    var toggle = document.querySelector(".theme-toggle");
    if (toggle) {
      updateToggleLabel(toggle);
      toggle.addEventListener("click", function () {
        var isDark = root.getAttribute("data-theme") === "dark";
        if (isDark) {
          root.removeAttribute("data-theme");
          localStorage.setItem("theme", "light");
        } else {
          root.setAttribute("data-theme", "dark");
          localStorage.setItem("theme", "dark");
        }
        updateToggleLabel(toggle);
      });
    }

    var navToggle = document.querySelector(".nav-toggle");
    var menu = document.querySelector("nav.menu");
    if (navToggle && menu) {
      navToggle.addEventListener("click", function () {
        menu.classList.toggle("open");
      });
    }
  });

  function updateToggleLabel(toggle) {
    var isDark = root.getAttribute("data-theme") === "dark";
    toggle.textContent = isDark ? "☀" : "☽";
    toggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
  }
})();

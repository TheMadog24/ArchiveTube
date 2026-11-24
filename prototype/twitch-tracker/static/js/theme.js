const themeToggle = document.getElementById("theme-toggle");
const themeIcon = themeToggle.querySelector(".theme-icon");
const themeLabel = themeToggle.querySelector(".theme-label");

function applyTheme(theme) {
    if (theme === "light") {
        document.documentElement.setAttribute("data-theme", "light");
        themeIcon.textContent = "☀";
        themeLabel.textContent = "Light Mode";
    } else {
        document.documentElement.removeAttribute("data-theme");
        themeIcon.textContent = "☾";
        themeLabel.textContent = "Dark Mode";
    }
}

// Load the saved theme, or use dark mode by default.
const savedTheme = localStorage.getItem("theme");

applyTheme(savedTheme === "light" ? "light" : "dark");

// Switch themes when the button is clicked.
themeToggle.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "light" ? "dark" : "light";

    localStorage.setItem("theme", newTheme);
    applyTheme(newTheme);
});


// Sidebar toggle
const sidebarToggle = document.getElementById("sidebar-toggle");
const pageContainer = document.querySelector(".page-container");

// Automatically collapse sidebar at 1200px and below
const sidebarBreakpoint = window.matchMedia("(max-width: 1200px)");

function updateSidebar() {
    if (sidebarBreakpoint.matches) {
        pageContainer.classList.add("sidebar-collapsed");
    } else {
        pageContainer.classList.remove("sidebar-collapsed");
    }
}

// Set initial sidebar state
updateSidebar();

// Update when crossing the breakpoint
sidebarBreakpoint.addEventListener("change", updateSidebar);

// Manual sidebar toggle
sidebarToggle.addEventListener("click", () => {
    pageContainer.classList.toggle("sidebar-collapsed");
});
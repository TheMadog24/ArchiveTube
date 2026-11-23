
const themeToggle = document.getElementById("theme-toggle");

function applyTheme(theme) {
    if (theme === "light") {
        document.documentElement.setAttribute("data-theme", "light");
        themeToggle.textContent = "Dark Mode";
    } else {
        document.documentElement.removeAttribute("data-theme");
        themeToggle.textContent = "Light Mode";
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

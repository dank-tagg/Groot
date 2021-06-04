document.addEventListener("DOMContentLoaded", function (event) {
    document.documentElement.setAttribute("data-theme", localStorage.theme);

    var themeSwitcher = document.getElementById("theme-switcher");

    themeSwitcher.onclick = function () {
        var currentTheme = document.documentElement.getAttribute("data-theme");

        var switchToTheme = currentTheme === "dark" ? "light" : "dark"
        localStorage.theme = switchToTheme

        document.documentElement.setAttribute("data-theme", switchToTheme);
    }
});

document.addEventListener("DOMContentLoaded", function (event) {
    var scrollToTopBtn = document.querySelector(".backToTop")
    var rootElement = document.documentElement

    function handleScroll() {
        // Do something on scroll
        var scrollTotal = rootElement.scrollHeight - rootElement.clientHeight
        if ((rootElement.scrollTop / scrollTotal) > 0.1) {
            // Show button
            scrollToTopBtn.classList.add("showButton")
        } else {
            // Hide button
            scrollToTopBtn.classList.remove("showButton")
        }
    }

    function scrollToTop() {
        // Scroll to top logic
        rootElement.scrollTo({
            top: 0,
            behavior: "smooth"
        })
    }
    scrollToTopBtn.addEventListener("click", scrollToTop)
    document.addEventListener("scroll", handleScroll)
});

document.addEventListener("DOMContentLoaded", function (event) {
    var searchButton = document.getElementById("showSearch");
    var searchBar = document.getElementById("searchBar");


    searchBar.addEventListener("keyup", function (e) {
        if (e.key == "Enter") {
            e.preventDefault();
            searchButton.click()
        }
    });

    searchButton.onclick = function () {
        let searched = document.getElementById("searchBar").value.trim();
        if (searched !== "") {
            var instance = new Mark(document.getElementById("main-content"));
            instance.unmark();
            instance.mark(searched, separateWordSearch = false);
            searchBar.value = ""
        }
    }
});
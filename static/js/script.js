const LANGS = ["ru", "kk", "en"];

function currentLang() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    if (!parts.length) return "ru";
    return LANGS.includes(parts[0]) ? parts[0] : "ru";
}

function currentPage() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    if (!parts.length) return "books";
    return LANGS.includes(parts[0]) ? parts[1] || "books" : parts[0];
}

function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[c]);
}

async function loadBooks() {
    const grid = document.getElementById("booksGrid");
    if (!grid) return;

    const lang = currentLang();
    const res = await fetch("/list");
    const books = await res.json();

    grid.innerHTML = "";

    books.forEach(book => {
        const name = (book.name && book.name[lang]) || Object.values(book.name || {})[0] || "No title";
        const author = (book.author && book.author[lang]) || Object.values(book.author || {})[0] || "";
        const img = "/images/" + (book.image || "no_img.png");

        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
            <img src="${img}">
            <div class="card-body">
                <h3>${escapeHtml(name)}</h3>
                <p>${escapeHtml(author)}</p>
            </div>
        `;

        // обработчик клика на карточку
        card.onclick = () => showModal(book, img);
        grid.appendChild(card);
    });
}

function showModal(book, img) {
    const lang = currentLang();

    document.getElementById("modalImg").src = img;
    document.getElementById("modalName").textContent =
        (book.name && book.name[lang]) || Object.values(book.name || {})[0] || "";
    document.getElementById("modalAuthor").textContent =
        (book.author && book.author[lang]) || Object.values(book.author || {})[0] || "";
    document.getElementById("modalYear").textContent = book.year || "";
    document.getElementById("modalIzdat").textContent = book.izdat || "";
    document.getElementById("modalAbout").textContent =
        (book.about && book.about[lang]) || Object.values(book.about || {})[0] || "Нет описания";

    const removeBtn = document.getElementById("removeBtn");
    if (removeBtn) {
        removeBtn.onclick = async () => {
            if (!confirm("Удалить книгу?")) return;
            await fetch("/remove", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: book.id })
            });
            closeModal();
            loadBooks();
        };
    }

    openModal();
}

function openModal() {
    const modalBg = document.getElementById("modalBg");
    if (modalBg) modalBg.style.display = "flex";
}

function closeModal() {
    const modalBg = document.getElementById("modalBg");
    if (modalBg) modalBg.style.display = "none";
}

function initAddForm() {
    const form = document.getElementById("addForm");
    if (!form) return;

    async function uploadImage() {
        const fi = document.getElementById("image");
        if (!fi || fi.files.length === 0) return null;
        const fd = new FormData();
        fd.append("file", fi.files[0]);
        const r = await fetch("/upload_image", { method: "POST", body: fd });
        const j = await r.json();
        return j.filename;
    }

    form.onsubmit = async e => {
        e.preventDefault();
        const filename = await uploadImage();
        const lang = currentLang();

        const payload = {
            name: document.getElementById("name").value,
            about: document.getElementById("about").value,
            author: document.getElementById("author").value,
            year: document.getElementById("year").value,
            izdat: document.getElementById("izdat").value,
            image: filename,
            lang
        };

        await fetch("/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        window.location.href = `/${lang}/books`;
    };
}

// навешиваем события после загрузки DOM
document.addEventListener("DOMContentLoaded", () => {
    const langSelect = document.getElementById("langSelect");
    if (langSelect) {
        const lang = currentLang();
        const page = currentPage();
        langSelect.value = lang;
        langSelect.onchange = () => window.location.href = `/${langSelect.value}/${page}`;
    }

    const closeBtn = document.getElementById("closeBtn");
    if (closeBtn) closeBtn.onclick = closeModal;

    const modalBg = document.getElementById("modalBg");
    if (modalBg) modalBg.onclick = e => {
        if (e.target.id === "modalBg") closeModal();
    };

    loadBooks();
    initAddForm();
});

const LANGS = ["ru","kk","en"];

function currentLang() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    return parts[0] && LANGS.includes(parts[0]) ? parts[0] : "ru";
}

function escapeHtml(s) {
    return String(s||"").replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" })[c]);
}

async function loadBooks() {
    const lang = currentLang();
    const res = await fetch("/list");
    const books = await res.json();
    const grid = document.getElementById("booksGrid");
    if (!grid) return;
    grid.innerHTML = "";

    books.forEach(book => {
        const name = (book.name && book.name[lang]) || Object.values(book.name||{})[0] || "No title";
        const author = (book.author && book.author[lang]) || Object.values(book.author||{})[0] || "";
        const img = "/images/" + (book.image || "no_img.png");

        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
            <img src="${img}" alt="">
            <div class="card-body">
                <h3>${escapeHtml(name)}</h3>
                <p>${escapeHtml(author)}</p>
            </div>
        `;
        card.addEventListener("click", () => showModal(book, img));
        grid.appendChild(card);
    });
}

function showModal(book, img) {
    const lang = currentLang();
    const title = (book.name && book.name[lang]) || Object.values(book.name||{})[0] || "";
    const about = (book.about && book.about[lang]) || Object.values(book.about||{})[0] || "";
    const author = (book.author && book.author[lang]) || Object.values(book.author||{})[0] || "";

    document.getElementById("modalImg").src = img;
    document.getElementById("modalName").textContent = title;
    document.getElementById("modalAuthor").textContent = author;
    document.getElementById("modalYear").textContent = book.year || "";
    document.getElementById("modalIzdat").textContent = book.izdat || "";
    document.getElementById("modalAbout").textContent = about || "Нет описания";

    const removeBtn = document.getElementById("removeBtn");
    removeBtn.onclick = async () => {
        if (!confirm(`Удалить "${title}"?`)) return;
        await fetch("/remove", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({id: book.id})
        });
        closeModal();
        loadBooks();
    };

    openModal();
}

function openModal() {
    document.getElementById("modalBg").style.display = "flex";
}

function closeModal() {
    document.getElementById("modalBg").style.display = "none";
}

document.addEventListener("click", (e) => {
    if (e.target && e.target.id === "modalBg") closeModal();
});
document.getElementById("closeBtn")?.addEventListener("click", closeModal);

/* Language selector */
document.addEventListener("DOMContentLoaded", () => {
    const langSelect = document.getElementById("langSelect");
    if (langSelect) {
        langSelect.value = currentLang();
        langSelect.addEventListener("change", () => {
            const target = langSelect.value;
            const parts = window.location.pathname.split("/").filter(Boolean);
            const page = parts[1] || "books";
            window.location.href = `/${target}/${page}`;
        });
    }
});

/* Add page */
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

    form.onsubmit = async (e) => {
        e.preventDefault();
        const filename = await uploadImage();
        const payload = {
            name: document.getElementById("name").value || "",
            about: document.getElementById("about").value || "",
            author: document.getElementById("author").value || "",
            year: document.getElementById("year").value || "",
            izdat: document.getElementById("izdat").value || "",
            image: filename,
            lang: currentLang()
        };
        await fetch("/add", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });
        window.location.href = `/${currentLang()}/books`;
    };
}

window.addEventListener("load", () => {
    loadBooks();
    initAddForm();
});

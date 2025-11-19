let books = [];

async function loadBooks() {
    const response = await fetch("/list");
    books = await response.json();
    const grid = document.getElementById("booksGrid");
    if (!grid) return;
    grid.innerHTML = "";
    books.forEach(book => {
        const img = "/images/" + (book.image || "no_img.png");
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
            <img src="${img}">
            <h3>${book.name}</h3>
            <p>${book.author}</p>
        `;
        card.onclick = () => showModal(book, img);
        grid.appendChild(card);
    });
}

function showModal(book, img) {
    document.getElementById("modalImg").src = img;
    document.getElementById("modalName").textContent = book.name;
    document.getElementById("modalAuthor").textContent = book.author;
    document.getElementById("modalYear").textContent = book.year;
    document.getElementById("modalIzdat").textContent = book.izdat;
    document.getElementById("modalAbout").textContent = book.about || book.about || "Нет описания";
    document.getElementById("modalBg").style.display = "flex";

    const removeBtn = document.getElementById("removeBtn");
    removeBtn.onclick = async function() {
        if (!confirm(`Удалить книгу "${book.name}"?`)) return;

        await fetch("/remove", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({id: book.id})
        });

        document.getElementById("modalBg").style.display = "none";
        loadBooks();
    };
}


document.getElementById("closeBtn")?.addEventListener("click", () => {
    document.getElementById("modalBg").style.display = "none";
});

document.getElementById("modalBg")?.addEventListener("click", (e) => {
    if (e.target === document.getElementById("modalBg")) {
        document.getElementById("modalBg").style.display = "none";
    }
});

window.onload = loadBooks;

// ================== Добавление книги ==================
function initAddForm() {
    const form = document.getElementById("addForm");
    if (!form) return;

    async function uploadImage() {
        const fileInput = document.getElementById("image");
        if (fileInput.files.length === 0) return null;

        let formData = new FormData();
        formData.append("file", fileInput.files[0]);

        let r = await fetch("/upload_image", {
            method: "POST",
            body: formData
        });
        let j = await r.json();
        return j.filename;
    }

    form.onsubmit = async function(e) {
        e.preventDefault();
        let filename = await uploadImage();
        const book = {
            name: document.getElementById("name").value,
            author: document.getElementById("author").value,
            year: document.getElementById("year").value,
            izdat: document.getElementById("izdat").value,
            about: document.getElementById("about")?.value || document.getElementById("about")?.value || "",
            image: filename
        };
        await fetch("/add", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(book)
        });
        window.location.href = "/books.html";
    };
}

initAddForm();

document.querySelectorAll('.book-link').forEach(btn => {
    btn.addEventListener('click', function() {
        document.getElementById('modalTitle').textContent = this.dataset.title;
        document.getElementById('modalAuthor').textContent = this.dataset.author;
        document.getElementById('modalYear').textContent = this.dataset.year;
        document.getElementById('modalPublisher').textContent = this.dataset.publisher;
        document.getElementById('modalDescription').textContent = this.dataset.description;
        document.getElementById('modalCover').src = this.dataset.coverUrl || '';
    });
});

document.addEventListener('alpine:init', () => {
    Alpine.data('libraryApp', () => ({
        view: 'list',
        books: [],
        meta: { page: 1, per_page: 20, total: 0 },
        selectedBook: null,
        sort: 'timestamp',
        order: 'desc',
        searchQuery: '',
        searchActive: false,
        loading: false,
        loadingMore: false,

        async init() {
            await this.fetchBooks();
            this.registerSW();
        },

        registerSW() {
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js').catch(() => {});
            }
        },

        // ── Chargement liste ────────────────────────────────────────────────

        async fetchBooks(append = false) {
            append ? (this.loadingMore = true) : (this.loading = true);
            try {
                const p = append ? this.meta.page + 1 : 1;
                const url = `/api/books?page=${p}&sort=${this.sort}&order=${this.order}`;
                const res = await fetch(url);
                if (res.status === 401) { location.href = '/login?next=/app'; return; }
                if (!res.ok) throw new Error(`Erreur ${res.status}`);
                const data = await res.json();
                this.books = append ? [...this.books, ...data.items] : data.items;
                this.meta = data.meta;
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
                this.loadingMore = false;
            }
        },

        // ── Recherche ───────────────────────────────────────────────────────

        async fetchSearch(append = false) {
            if (!this.searchQuery.trim()) return;
            append ? (this.loadingMore = true) : (this.loading = true);
            try {
                const p = append ? this.meta.page + 1 : 1;
                const q = encodeURIComponent(this.searchQuery);
                const url = `/api/search?q=${q}&page=${p}&sort=${this.sort}&order=${this.order}`;
                const res = await fetch(url);
                if (res.status === 401) { location.href = '/login?next=/app'; return; }
                const data = await res.json();
                this.books = append ? [...this.books, ...data.items] : data.items;
                this.meta = data.meta;
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
                this.loadingMore = false;
            }
        },

        async doSearch() {
            if (!this.searchQuery.trim()) {
                await this.clearSearch();
                return;
            }
            this.searchActive = true;
            this.view = 'list';
            await this.fetchSearch();
        },

        async clearSearch() {
            this.searchQuery = '';
            this.searchActive = false;
            this.view = 'list';
            await this.fetchBooks();
        },

        // ── Fiche livre ─────────────────────────────────────────────────────

        async openBook(id) {
            this.loading = true;
            try {
                const res = await fetch(`/api/books/${id}`);
                if (res.status === 401) { location.href = '/login?next=/app'; return; }
                this.selectedBook = await res.json();
                this.view = 'detail';
                window.scrollTo(0, 0);
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        },

        back() {
            this.view = 'list';
            this.selectedBook = null;
        },

        // ── Tri ─────────────────────────────────────────────────────────────

        async applySort(newSort) {
            if (this.sort === newSort) {
                this.order = this.order === 'asc' ? 'desc' : 'asc';
            } else {
                this.sort = newSort;
                this.order = newSort === 'timestamp' ? 'desc' : 'asc';
            }
            if (this.searchActive && this.searchQuery) {
                await this.fetchSearch();
            } else {
                await this.fetchBooks();
            }
        },

        // ── "Charger plus" ──────────────────────────────────────────────────

        async loadMore() {
            if (this.searchActive) {
                await this.fetchSearch(true);
            } else {
                await this.fetchBooks(true);
            }
        },

        // ── Getters ─────────────────────────────────────────────────────────

        get hasMore() {
            return this.books.length < this.meta.total;
        },

        // ── Helpers ─────────────────────────────────────────────────────────

        orderIcon(s) {
            if (this.sort !== s) return '↕';
            return this.order === 'asc' ? '↑' : '↓';
        },

        authorNames(authors) {
            return authors.map(a => a.name).join(', ');
        },

        formatSize(bytes) {
            if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} Ko`;
            return `${(bytes / 1024 / 1024).toFixed(1)} Mo`;
        },

        fmtColor(fmt) {
            const c = {
                EPUB: '#2563eb', KEPUB: '#7c3aed', PDF: '#dc2626',
                MOBI: '#d97706', AZW3: '#b45309', TXT: '#6b7280',
            };
            return c[fmt] ?? '#374151';
        },

        pubYear(pubdate) {
            if (!pubdate) return '';
            return new Date(pubdate).getFullYear();
        },

        stars(rating) {
            if (!rating) return '';
            const n = Math.floor(rating / 2);
            return '★'.repeat(n) + '☆'.repeat(5 - n);
        },
    }));
});

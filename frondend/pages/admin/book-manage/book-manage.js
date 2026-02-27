const api = require('../../../utils/request');

Page({
    data: {
        keyword: '',
        currentFilter: 'all',
        books: [],
        page: 1,
        hasMore: true,
        loading: false
    },

    onLoad() {
        this.loadBooks();
    },

    onPullDownRefresh() {
        this.setData({ page: 1, books: [] });
        this.loadBooks().then(() => {
            wx.stopPullDownRefresh();
        });
    },

    loadBooks() {
        if (this.data.loading) return;
        this.setData({ loading: true });

        const params = {
            page: this.data.page,
            limit: 20,
            keyword: this.data.keyword || undefined,
            filter: this.data.currentFilter !== 'all' ? this.data.currentFilter : undefined
        };

        return api.get('/admin/books', params).then(data => {
            const newBooks = this.data.page === 1 ? data.items : [...this.data.books, ...data.items];
            this.setData({
                books: newBooks,
                hasMore: data.items.length === 20,
                page: this.data.page + 1
            });
        }).finally(() => {
            this.setData({ loading: false });
        });
    },

    loadMore() {
        if (this.data.hasMore) {
            this.loadBooks();
        }
    },

    onSearchInput(e) {
        this.setData({ keyword: e.detail.value });
    },

    doSearch() {
        this.setData({ page: 1, books: [] });
        this.loadBooks();
    },

    setFilter(e) {
        this.setData({
            currentFilter: e.currentTarget.dataset.filter,
            page: 1,
            books: []
        });
        this.loadBooks();
    },

    onAction(e) {
        const book = e.currentTarget.dataset.book;
        wx.showActionSheet({
            itemList: ['编辑', '修改库存', '删除'],
            success: (res) => {
                switch (res.tapIndex) {
                    case 0:
                        this.editBook({ currentTarget: { dataset: { isbn: book.isbn } } });
                        break;
                    case 1:
                        this.modifyStock(book);
                        break;
                    case 2:
                        this.deleteBook(book.isbn);
                        break;
                }
            }
        });
        e.stopPropagation();
    },

    editBook(e) {
        wx.navigateTo({
            url: `/pages/admin/book-edit/book-edit?isbn=${e.currentTarget.dataset.isbn}`
        });
    },

    modifyStock(book) {
        wx.showModal({
            title: '修改库存',
            content: `当前库存: ${book.stock}，总库存: ${book.total}`,
            editable: true,
            placeholderText: '输入新库存数量',
            success: (res) => {
                if (res.confirm && res.content) {
                    const newStock = parseInt(res.content);
                    if (!isNaN(newStock) && newStock >= 0) {
                        api.put(`/admin/books/${book.isbn}/stock`, { stock: newStock }).then(() => {
                            wx.showToast({ title: '修改成功' });
                            this.onPullDownRefresh();
                        });
                    }
                }
            }
        });
    },

    deleteBook(isbn) {
        wx.showModal({
            title: '确认删除',
            content: '删除后不可恢复，确定删除？',
            confirmColor: '#ff4d4f',
            success: (res) => {
                if (res.confirm) {
                    api.del(`/admin/books/${isbn}`).then(() => {
                        wx.showToast({ title: '已删除' });
                        this.onPullDownRefresh();
                    });
                }
            }
        });
    },

    scanAdd() {
        wx.scanCode({
            success: (res) => {
                wx.navigateTo({
                    url: `/pages/admin/book-add/book-add?isbn=${res.result}`
                });
            }
        });
    },

    goAdd() {
        wx.navigateTo({ url: '/pages/admin/book-add/book-add' });
    }
});

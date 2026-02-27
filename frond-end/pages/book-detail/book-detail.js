const api = require('../../utils/request');

Page({
    data: {
        book: null,
        isBorrowed: false,
        loading: true,
        fromScan: false
    },

    onLoad(options) {
        if (options.isbn) {
            this.setData({ fromScan: options.from === 'scan' });
            this.loadBook(options.isbn);
        } else if (options.keyword) {
            this.searchBook(options.keyword);
        } else {
            this.setData({ loading: false });
            wx.showToast({ title: '缺少查询参数', icon: 'none' });
        }
    },

    loadBook(isbn) {
        api.get(`/books/${isbn}`)
            .then((data) => {
                this.setData({
                    book: data,
                    isBorrowed: data.user_borrow_id !== null,
                    loading: false
                });
            })
            .catch(() => {
                this.setData({ loading: false });
                if (this.data.fromScan) {
                    wx.showModal({
                        title: '图书未入库',
                        content: '请联系管理员录入新书',
                        showCancel: false
                    });
                } else {
                    wx.showToast({ title: '未找到图书', icon: 'none' });
                }
            });
    },

    searchBook(keyword) {
        api.get('/books/search', { keyword, limit: 1 })
            .then((data) => {
                const list = Array.isArray(data) ? data : (data.items || []);
                if (list.length === 0) {
                    this.setData({ loading: false });
                    wx.showToast({ title: '未找到图书', icon: 'none' });
                    return;
                }

                this.loadBook(list[0].isbn);
            })
            .catch(() => {
                this.setData({ loading: false });
            });
    },

    onBorrow() {
        if (!this.data.book) {
            return;
        }

        api.post('/borrows', { isbn: this.data.book.isbn })
            .then(() => {
                wx.showToast({ title: '借阅成功', icon: 'success' });
                this.setData({
                    isBorrowed: true,
                    'book.stock': Math.max((this.data.book.stock || 1) - 1, 0)
                });
            });
    },

    onReturn() {
        if (!this.data.book || !this.data.book.user_borrow_id) {
            return;
        }

        api.put(`/borrows/${this.data.book.user_borrow_id}/return`)
            .then(() => {
                wx.showToast({ title: '归还成功', icon: 'success' });
                this.setData({
                    isBorrowed: false,
                    'book.stock': (this.data.book.stock || 0) + 1,
                    'book.user_borrow_id': null
                });
            });
    }
});

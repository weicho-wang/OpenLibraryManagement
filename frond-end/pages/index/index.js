const api = require('../../utils/request');
const auth = require('../../utils/auth');

Page({
    data: {
        keyword: '',
        recentBooks: []
    },

    onLoad() {
        if (!auth.checkLogin()) {
            auth.login()
                .then(() => this.loadRecentBooks())
                .catch(() => {
                    wx.showToast({ title: '登录失败，请重试', icon: 'none' });
                });
        } else {
            this.loadRecentBooks();
        }
    },

    onScan() {
        wx.scanCode({
            onlyFromCamera: true,
            scanType: ['barCode'],
            success: (res) => {
                const isbn = res.result;
                wx.navigateTo({
                    url: `/pages/book-detail/book-detail?isbn=${isbn}&from=scan`
                });
            },
            fail: () => {
                wx.showToast({ title: '扫码取消', icon: 'none' });
            }
        });
    },

    onInput(e) {
        this.setData({ keyword: e.detail.value });
    },

    onSearch() {
        if (!this.data.keyword.trim()) {
            return;
        }

        wx.navigateTo({
            url: `/pages/book-detail/book-detail?keyword=${this.data.keyword.trim()}`
        });
    },

    loadRecentBooks() {
        api.get('/books/recent', { limit: 5 })
            .then((data) => {
                this.setData({ recentBooks: data || [] });
            })
            .catch(() => {
                this.setData({ recentBooks: [] });
            });
    },

    goDetail(e) {
        const isbn = e.detail && e.detail.isbn ? e.detail.isbn : e.currentTarget.dataset.isbn;
        if (!isbn) {
            return;
        }

        wx.navigateTo({
            url: `/pages/book-detail/book-detail?isbn=${isbn}`
        });
    }
});

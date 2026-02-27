const api = require('../../utils/request');

Page({
    data: {
        borrows: [],
        activeTab: 'current'
    },

    onShow() {
        this.loadBorrows();
    },

    loadBorrows() {
        const status = this.data.activeTab === 'current' ? 'active' : 'returned';
        api.get('/borrows/my', { status })
            .then((data) => {
                this.setData({ borrows: data || [] });
            })
            .catch(() => {
                this.setData({ borrows: [] });
            });
    },

    switchTab(e) {
        this.setData({ activeTab: e.currentTarget.dataset.tab }, () => {
            this.loadBorrows();
        });
    },

    quickReturn() {
        wx.scanCode({
            onlyFromCamera: true,
            scanType: ['barCode'],
            success: (res) => {
                const isbn = res.result;
                const record = this.data.borrows.find((item) => item.book_isbn === isbn);
                if (record) {
                    this.doReturn(record.id);
                } else {
                    wx.showToast({ title: '未找到该书的借阅记录', icon: 'none' });
                }
            }
        });
    },

    doReturn(arg) {
        const borrowId = typeof arg === 'object' ? arg.currentTarget.dataset.id : arg;
        if (!borrowId) {
            return;
        }

        api.put(`/borrows/${borrowId}/return`)
            .then(() => {
                wx.showToast({ title: '归还成功', icon: 'success' });
                this.loadBorrows();
            });
    }
});

const api = require('../../../utils/request');

Page({
    data: {
        overdues: [],
        total: 0
    },

    onLoad() {
        this.loadData();
    },

    onPullDownRefresh() {
        this.loadData().then(() => wx.stopPullDownRefresh());
    },

    loadData() {
        return api.get('/borrows/admin/overdue').then(data => {
            const now = new Date();
            const overdues = data.map(item => {
                const due = new Date(item.due_date);
                const days = Math.floor((now - due) / (1000 * 60 * 60 * 24));
                return { ...item, overdue_days: days };
            }).sort((a, b) => b.overdue_days - a.overdue_days);

            this.setData({
                overdues: overdues,
                total: overdues.length
            });
        });
    },

    remind(e) {
        const id = e.currentTarget.dataset.id;
        api.post(`/admin/borrows/${id}/remind`).then(() => {
            wx.showToast({ title: '已发送催还通知' });
        });
    },

    batchRemind() {
        wx.showModal({
            title: '批量催还',
            content: `将向全部${this.data.total}位逾期用户发送催还通知`,
            success: (res) => {
                if (res.confirm) {
                    api.post('/admin/borrows/batch-remind').then(() => {
                        wx.showToast({ title: '批量催还已发送' });
                    });
                }
            }
        });
    }
});

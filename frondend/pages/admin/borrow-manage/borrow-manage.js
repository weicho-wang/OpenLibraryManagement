const api = require('../../../utils/request');

Page({
    data: {
        activeTab: 'active',
        records: [],
        counts: { active: 0, returned: 0, overdue: 0 }
    },

    onLoad() {
        this.loadData();
        this.loadCounts();
    },

    onShow() {
        this.loadData();
    },

    switchTab(e) {
        this.setData({ activeTab: e.currentTarget.dataset.tab }, () => {
            this.loadData();
        });
    },

    loadData() {
        const status = this.data.activeTab;
        api.get('/admin/borrows', { status }).then(data => {
            const now = new Date();
            const records = data.map(r => ({
                ...r,
                is_overdue: new Date(r.due_date) < now && r.status === 'active'
            }));
            this.setData({ records });
        });
    },

    loadCounts() {
        api.get('/admin/borrows/counts').then(data => {
            this.setData({ counts: data });
        });
    },

    remindReturn(e) {
        const id = e.currentTarget.dataset.id;
        api.post(`/admin/borrows/${id}/remind`).then(() => {
            wx.showToast({ title: '催还通知已发送' });
        });
    },

    forceReturn(e) {
        const id = e.currentTarget.dataset.id;
        wx.showModal({
            title: '确认强制归还',
            content: '此操作将直接完成归还，无需用户扫码',
            success: (res) => {
                if (res.confirm) {
                    api.put(`/admin/borrows/${id}/force-return`).then(() => {
                        wx.showToast({ title: '已强制归还' });
                        this.loadData();
                        this.loadCounts();
                    });
                }
            }
        });
    }
});

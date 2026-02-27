const api = require('../../../utils/request');
const auth = require('../../../utils/auth');

Page({
    data: {
        today: '',
        stats: {
            totalBooks: 0,
            newBooksToday: 0,
            activeBorrows: 0,
            todayBorrows: 0,
            overdueCount: 0,
            totalUsers: 0,
            newUsersToday: 0
        },
        recentActivities: []
    },

    onLoad() {
        this.checkAdmin();
        this.setToday();
        this.loadStats();
        this.loadActivities();
    },

    onShow() {
        this.loadStats();
    },

    checkAdmin() {
        const user = auth.getUser();
        if (!user || !user.is_admin) {
            wx.showModal({
                title: '无权限',
                content: '需要管理员权限',
                showCancel: false,
                success: () => wx.switchTab({ url: '/pages/index/index' })
            });
        }
    },

    setToday() {
        const date = new Date();
        this.setData({
            today: `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
        });
    },

    loadStats() {
        api.get('/admin/stats').then(data => {
            this.setData({ stats: data });
        });
    },

    loadActivities() {
        api.get('/admin/activities', { limit: 10 }).then(data => {
            this.setData({ recentActivities: data });
        });
    },

    goToBooks() {
        wx.navigateTo({ url: '/pages/admin/book-manage/book-manage' });
    },

    goToBorrows() {
        wx.navigateTo({ url: '/pages/admin/borrow-manage/borrow-manage' });
    },

    goToOverdue() {
        wx.navigateTo({ url: '/pages/admin/overdue-list/overdue-list' });
    },

    scanAddBook() {
        wx.scanCode({
            onlyFromCamera: true,
            scanType: ['barCode'],
            success: (res) => {
                wx.navigateTo({
                    url: `/pages/admin/book-add/book-add?isbn=${res.result}`
                });
            }
        });
    },

    exportData() {
        wx.showActionSheet({
            itemList: ['导出图书清单', '导出借阅记录', '导出逾期名单'],
            success: (res) => {
                const types = ['books', 'borrows', 'overdue'];
                this.doExport(types[res.tapIndex]);
            }
        });
    },

    doExport(type) {
        api.get(`/admin/export?type=${type}`).then(data => {
            wx.setClipboardData({
                data: data.download_url,
                success: () => wx.showToast({ title: '链接已复制' })
            });
        });
    }
});

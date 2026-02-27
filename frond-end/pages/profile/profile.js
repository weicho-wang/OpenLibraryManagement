const auth = require('../../utils/auth');

Page({
    data: {
        user: null
    },

    onShow() {
        this.setData({ user: auth.getUser() || {} });
    },

    toBorrows() {
        wx.switchTab({ url: '/pages/borrow-list/borrow-list' });
    },

    goAdmin() {
        const user = auth.getUser();
        if (user && user.is_admin) {
            wx.navigateTo({ url: '/pages/admin/dashboard/dashboard' });
        } else {
            wx.showToast({ title: '无权限', icon: 'none' });
        }
    },

    logout() {
        wx.showModal({
            title: '退出登录',
            content: '确认退出当前账号吗？',
            success: (res) => {
                if (res.confirm) {
                    auth.logout();
                    wx.showToast({ title: '已退出', icon: 'success' });
                    setTimeout(() => {
                        wx.switchTab({ url: '/pages/index/index' });
                    }, 500);
                }
            }
        });
    }
});

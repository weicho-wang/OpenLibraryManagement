const api = require('../../../utils/request');

Page({
  data: {
    keyword: '',
    filter: 'all',
    users: [],
    page: 1,
    hasMore: true,
    loading: false,
    stats: {
      total: 0,
      admins: 0,
      active_today: 0
    },
    showModal: false,
    currentUser: null
  },

  onLoad() {
    this.loadStats();
    this.loadUsers();
  },

  onPullDownRefresh() {
    this.setData({ page: 1, users: [] });
    Promise.all([
      this.loadStats(),
      this.loadUsers()
    ]).then(() => {
      wx.stopPullDownRefresh();
    });
  },

  loadStats() {
    return api.get('/admin/users/stats').then(data => {
      this.setData({ stats: data });
    });
  },

  loadUsers() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    const params = {
      page: this.data.page,
      limit: 20,
      keyword: this.data.keyword || undefined,
      filter: this.data.filter !== 'all' ? this.data.filter : undefined
    };

    return api.get('/admin/users', params).then(data => {
      const newUsers = this.data.page === 1 ? data.items : [...this.data.users, ...data.items];
      this.setData({
        users: newUsers,
        hasMore: data.items.length === 20,
        page: this.data.page + 1
      });
    }).finally(() => {
      this.setData({ loading: false });
    });
  },

  loadMore() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadUsers();
    }
  },

  onSearchInput(e) {
    this.setData({ keyword: e.detail.value });
  },

  doSearch() {
    this.setData({ page: 1, users: [] });
    this.loadUsers();
  },

  setFilter(e) {
    this.setData({
      filter: e.currentTarget.dataset.filter,
      page: 1,
      users: []
    });
    this.loadUsers();
  },

  onAction(e) {
    const user = e.currentTarget.dataset.user;
    this.setData({
      showModal: true,
      currentUser: user
    });
    e.stopPropagation();
  },

  closeModal() {
    this.setData({ showModal: false, currentUser: null });
  },

  stopPropagation() {},

  toggleAdmin(e) {
    const user = this.data.currentUser;
    const newStatus = e.detail.value;

    wx.showModal({
      title: newStatus ? '设为管理员' : '取消管理员',
      content: newStatus
        ? `确定将用户 ${user.id} 设为管理员？`
        : `确定取消用户 ${user.id} 的管理员权限？`,
      success: (res) => {
        if (res.confirm) {
          api.put(`/admin/users/${user.id}/admin`, { is_admin: newStatus }).then(() => {
            const updatedUsers = this.data.users.map(u => {
              if (u.id === user.id) u.is_admin = newStatus;
              return u;
            });
            this.setData({
              users: updatedUsers,
              'currentUser.is_admin': newStatus
            });
            wx.showToast({ title: '已更新' });
            this.loadStats();
          }).catch(() => {
            this.setData({ 'currentUser.is_admin': !newStatus });
          });
        } else {
          this.setData({ 'currentUser.is_admin': !newStatus });
        }
      }
    });
  },

  viewUserBorrows() {
    const userId = this.data.currentUser.id;
    this.closeModal();
    wx.navigateTo({
      url: `/pages/admin/user-borrows/user-borrows?userId=${userId}`
    });
  },

  banUser() {
    const user = this.data.currentUser;
    wx.showModal({
      title: '禁用账号',
      content: '禁用后该用户将无法登录，确定继续？',
      confirmColor: '#ff4d4f',
      success: (res) => {
        if (res.confirm) {
          api.put(`/admin/users/${user.id}/ban`).then(() => {
            wx.showToast({ title: '已禁用' });
            this.closeModal();
            this.onPullDownRefresh();
          });
        }
      }
    });
  },

  viewDetail(e) {
    const user = this.data.users.find(u => u.id === e.currentTarget.dataset.id);
    this.setData({
      showModal: true,
      currentUser: user
    });
  }
});

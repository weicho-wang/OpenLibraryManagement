const api = require('../../../utils/request');

Page({
    data: {
        userId: null,
        records: [],
        stats: {}
    },

    onLoad(options) {
        this.setData({ userId: options.userId });
        this.loadData();
    },

    loadData() {
        api.get(`/admin/users/${this.data.userId}/borrows`).then(data => {
            this.setData({
                records: data.records,
                stats: data.stats
            });
        });
    }
});

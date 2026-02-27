Page({
    data: {
        result: ''
    },

    onScan() {
        wx.scanCode({
            onlyFromCamera: true,
            scanType: ['barCode'],
            success: (res) => {
                const isbn = res.result;
                this.setData({ result: isbn });
                wx.navigateTo({
                    url: `/pages/book-detail/book-detail?isbn=${isbn}&from=scan`
                });
            },
            fail: () => {
                wx.showToast({ title: '扫码取消', icon: 'none' });
            }
        });
    }
});

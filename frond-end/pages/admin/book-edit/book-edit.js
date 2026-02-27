const api = require('../../../utils/request');
const config = require('../../../config');

Page({
    data: {
        isbn: '',
        book: {},
        originalBook: {},
        tagsText: '',
        stats: {
            total_borrows: 0,
            active_borrows: 0
        },
        borrowHistory: []
    },

    onLoad(options) {
        if (!options.isbn) {
            wx.showToast({ title: '参数错误', icon: 'error' });
            return wx.navigateBack();
        }

        this.setData({ isbn: options.isbn });
        this.loadBook();
        this.loadHistory();
    },

    loadBook() {
        api.get(`/books/${this.data.isbn}`).then(data => {
            const tagsText = (data.tags || []).join(' ');
            this.setData({
                book: data,
                originalBook: JSON.parse(JSON.stringify(data)),
                tagsText: tagsText
            });
        }).catch(() => {
            wx.showToast({ title: '图书不存在', icon: 'error' });
            wx.navigateBack();
        });
    },

    loadHistory() {
        api.get(`/admin/books/${this.data.isbn}/history`).then(data => {
            const history = data.map(item => ({
                ...item,
                status_text: item.status === 'active' ? '借阅中' :
                    item.status === 'returned' ? '已归还' : '已逾期'
            }));
            this.setData({
                borrowHistory: history,
                stats: {
                    total_borrows: history.length,
                    active_borrows: history.filter(h => h.status === 'active').length
                }
            });
        });
    },

    onInput(e) {
        const field = e.currentTarget.dataset.field;
        this.setData({
            [`book.${field}`]: e.detail.value
        });
    },

    onStockInput(e) {
        const val = parseInt(e.detail.value) || 0;
        this.setData({ 'book.stock': Math.max(0, val) });
    },

    changeStock(e) {
        const delta = parseInt(e.currentTarget.dataset.delta);
        const newStock = this.data.book.stock + delta;
        if (newStock >= 0) {
            this.setData({ 'book.stock': newStock });
        }
    },

    onTagsInput(e) {
        const tags = e.detail.value.split(/[\s,，]+/).filter(t => t);
        this.setData({
            tagsText: e.detail.value,
            'book.tags': tags
        });
    },

    changeCover() {
        wx.showActionSheet({
            itemList: ['从相册选择', '输入链接', '恢复默认'],
            success: (res) => {
                switch (res.tapIndex) {
                    case 0:
                        this.chooseImage();
                        break;
                    case 1:
                        this.inputUrl();
                        break;
                    case 2:
                        this.setData({ 'book.cover_url': '' });
                        break;
                }
            }
        });
    },

    chooseImage() {
        wx.chooseMedia({
            count: 1,
            mediaType: ['image'],
            success: (res) => {
                const tempFile = res.tempFiles[0].tempFilePath;
                this.uploadImage(tempFile);
            }
        });
    },

    uploadImage(filePath) {
        wx.uploadFile({
            url: `${config.baseUrl}/admin/upload`,
            filePath: filePath,
            name: 'file',
            header: {
                Authorization: `Bearer ${wx.getStorageSync('token')}`
            },
            success: (res) => {
                const data = JSON.parse(res.data);
                this.setData({ 'book.cover_url': data.url });
            }
        });
    },

    inputUrl() {
        wx.showModal({
            title: '输入封面链接',
            editable: true,
            success: (res) => {
                if (res.confirm && res.content) {
                    this.setData({ 'book.cover_url': res.content });
                }
            }
        });
    },

    reset() {
        const original = JSON.parse(JSON.stringify(this.data.originalBook));
        this.setData({
            book: original,
            tagsText: (original.tags || []).join(' ')
        });
        wx.showToast({ title: '已重置', icon: 'none' });
    },

    save() {
        if (!this.data.book.title.trim()) {
            return wx.showToast({ title: '书名不能为空', icon: 'none' });
        }

        const updateData = {
            title: this.data.book.title,
            author: this.data.book.author,
            publisher: this.data.book.publisher,
            publish_date: this.data.book.publish_date,
            stock: parseInt(this.data.book.stock) || 0,
            cover_url: this.data.book.cover_url,
            summary: this.data.book.summary,
            tags: this.data.book.tags
        };

        wx.showLoading({ title: '保存中...' });

        api.put(`/admin/books/${this.data.isbn}`, updateData).then(() => {
            wx.showToast({ title: '保存成功', icon: 'success' });
            this.setData({ originalBook: this.data.book });
        }).catch(err => {
            wx.showToast({ title: err.detail || '保存失败', icon: 'none' });
        }).finally(() => {
            wx.hideLoading();
        });
    },

    deleteBook() {
        wx.showModal({
            title: '危险操作',
            content: '删除后不可恢复，确定删除这本图书？',
            confirmColor: '#ff4d4f',
            success: (res) => {
                if (res.confirm) {
                    api.del(`/admin/books/${this.data.isbn}`).then(() => {
                        wx.showToast({ title: '已删除' });
                        setTimeout(() => {
                            wx.navigateBack();
                        }, 1000);
                    }).catch(err => {
                        wx.showToast({
                            title: err.detail || '删除失败',
                            icon: 'none'
                        });
                    });
                }
            }
        });
    }
});

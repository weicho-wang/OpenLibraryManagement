const api = require('../../../utils/request');

Page({
    data: {
        isbn: '',
        book: {
            isbn: '',
            title: '',
            author: '',
            publisher: '',
            publish_date: '',
            stock: 1,
            cover_url: '',
            summary: '',
            tags: []
        },
        tagsText: '',
        isLoading: false
    },

    onLoad(options) {
        if (options.isbn) {
            this.setData({
                isbn: options.isbn,
                'book.isbn': options.isbn
            });
            this.autoFill();
        } else {
            this.reScan();
        }
    },

    reScan() {
        wx.scanCode({
            onlyFromCamera: true,
            scanType: ['barCode'],
            success: (res) => {
                this.setData({
                    isbn: res.result,
                    'book.isbn': res.result
                });
                this.autoFill();
            },
            fail: () => {
                wx.navigateBack();
            }
        });
    },

    autoFill() {
        if (this.data.isLoading) return;
        this.setData({ isLoading: true });

        wx.showLoading({ title: '查询中...' });

        api.get(`/books/${this.data.isbn}/query-isbn`).then(data => {
            const book = { ...this.data.book, ...data };
            this.setData({
                book: book,
                tagsText: (data.tags || []).join(' ')
            });
            wx.showToast({ title: '查询成功', icon: 'success' });
        }).catch(() => {
            wx.showToast({ title: '未找到图书信息，请手动填写', icon: 'none' });
        }).finally(() => {
            this.setData({ isLoading: false });
            wx.hideLoading();
        });
    },

    onInput(e) {
        const field = e.currentTarget.dataset.field;
        const value = e.detail.value;
        this.setData({
            [`book.${field}`]: value
        });
    },

    onTagsInput(e) {
        const tags = e.detail.value.split(/[\s,，]+/).filter(t => t);
        this.setData({
            tagsText: e.detail.value,
            'book.tags': tags
        });
    },

    onImageError() {
        this.setData({ 'book.cover_url': '' });
        wx.showToast({ title: '封面加载失败', icon: 'none' });
    },

    submit() {
        if (!this.data.book.title.trim()) {
            wx.showToast({ title: '请输入书名', icon: 'none' });
            return;
        }

        const stock = parseInt(this.data.book.stock) || 1;

        api.post('/books', {
            ...this.data.book,
            stock: stock,
            total: stock
        }).then(() => {
            wx.showModal({
                title: '入库成功',
                content: '是否继续录入下一本？',
                success: (res) => {
                    if (res.confirm) {
                        this.reScan();
                    } else {
                        wx.navigateBack();
                    }
                }
            });
        }).catch(err => {
            wx.showToast({
                title: err.detail || '入库失败',
                icon: 'none'
            });
        });
    }
});

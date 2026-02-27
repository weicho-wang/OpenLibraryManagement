const config = require('../config');

const request = (options) => {
    return new Promise((resolve, reject) => {
        const token = wx.getStorageSync('token');

        wx.request({
            url: config.baseUrl + options.url,
            method: options.method || 'GET',
            data: options.data,
            header: {
                'Content-Type': 'application/json',
                Authorization: token ? `Bearer ${token}` : ''
            },
            timeout: config.timeout,
            success: (res) => {
                if (res.statusCode === 200) {
                    resolve(res.data);
                } else if (res.statusCode === 401) {
                    wx.removeStorageSync('token');
                    wx.removeStorageSync('userInfo');
                    wx.navigateTo({ url: '/pages/index/index' });
                    reject(new Error('登录已过期'));
                } else {
                    wx.showToast({
                        title: (res.data && (res.data.detail || res.data.message)) || '请求失败',
                        icon: 'none'
                    });
                    reject(res.data || new Error('请求失败'));
                }
            },
            fail: (err) => {
                wx.showToast({ title: '网络错误', icon: 'none' });
                reject(err);
            }
        });
    });
};

module.exports = {
    get: (url, params) => request({ url, method: 'GET', data: params }),
    post: (url, data) => request({ url, method: 'POST', data }),
    put: (url, data) => request({ url, method: 'PUT', data }),
    del: (url) => request({ url, method: 'DELETE' })
};

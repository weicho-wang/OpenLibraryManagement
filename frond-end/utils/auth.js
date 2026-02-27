const api = require('./request');

const auth = {
    login() {
        return new Promise((resolve, reject) => {
            wx.login({
                success: (res) => {
                    if (!res.code) {
                        reject(new Error('微信登录失败'));
                        return;
                    }

                    api.post('/auth/wx-login', { code: res.code })
                        .then((data) => {
                            wx.setStorageSync('token', data.access_token);
                            wx.setStorageSync('userInfo', data.user);
                            resolve(data);
                        })
                        .catch(reject);
                },
                fail: reject
            });
        });
    },

    checkLogin() {
        const token = wx.getStorageSync('token');
        return !!token;
    },

    getUser() {
        return wx.getStorageSync('userInfo');
    },

    logout() {
        wx.removeStorageSync('token');
        wx.removeStorageSync('userInfo');
    }
};

module.exports = auth;

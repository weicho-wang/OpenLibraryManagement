const config = {
    dev: {
        baseUrl: 'http://localhost:8000/api/v1',
        timeout: 10000
    },
    prod: {
        baseUrl: 'https://your-domain.com/api/v1',
        timeout: 10000
    }
};

const env = 'dev';

module.exports = config[env];

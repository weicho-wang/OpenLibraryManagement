-- 数据库: library
-- 编码: UTF-8
-- 时区: Asia/Shanghai

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    openid          VARCHAR(100) NOT NULL UNIQUE,
    nickname        VARCHAR(50),
    avatar_url      VARCHAR(500),
    is_admin        SMALLINT DEFAULT 0 CHECK (is_admin IN (0, 1)),
    status          VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'banned', 'deleted')),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT idx_openid UNIQUE (openid)
);

CREATE INDEX idx_users_created ON users(created_at DESC);
CREATE INDEX idx_users_admin ON users(is_admin) WHERE is_admin = 1;

CREATE TABLE books (
    isbn            VARCHAR(20) PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    author          VARCHAR(200),
    publisher       VARCHAR(100),
    publish_date    VARCHAR(20),
    cover_url       VARCHAR(500),
    summary         TEXT,
    tags            VARCHAR(50)[],
    stock           INTEGER NOT NULL DEFAULT 1 CHECK (stock >= 0),
    total           INTEGER NOT NULL DEFAULT 1 CHECK (total >= 0),
    location        VARCHAR(50),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_stock_valid CHECK (stock <= total)
);

CREATE INDEX idx_books_author ON books(author);
CREATE INDEX idx_books_tags ON books USING gin(tags);
CREATE INDEX idx_books_created ON books(created_at DESC);
CREATE INDEX idx_books_stock ON books(stock) WHERE stock < 3;

CREATE TABLE borrow_records (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    book_isbn       VARCHAR(20) NOT NULL REFERENCES books(isbn) ON DELETE RESTRICT,
    borrowed_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    due_date        TIMESTAMP WITH TIME ZONE NOT NULL,
    returned_at     TIMESTAMP WITH TIME ZONE,
    status          VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'returned', 'overdue', 'lost')),
    return_method   VARCHAR(20),
    notes           VARCHAR(500),
    remind_count    INTEGER DEFAULT 0,
    last_remind_at  TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_borrows_user ON borrow_records(user_id, status);
CREATE INDEX idx_borrows_book ON borrow_records(book_isbn, status);
CREATE INDEX idx_borrows_status ON borrow_records(status) WHERE status = 'active';
CREATE INDEX idx_borrows_due ON borrow_records(due_date) WHERE status = 'active';

CREATE TABLE system_logs (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(50) NOT NULL,
    target_type     VARCHAR(50),
    target_id       VARCHAR(50),
    detail          JSONB,
    ip_address      INET,
    user_agent      VARCHAR(500),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_user ON system_logs(user_id, created_at DESC);
CREATE INDEX idx_logs_action ON system_logs(action, created_at DESC);
CREATE INDEX idx_logs_created ON system_logs(created_at DESC);

CREATE TABLE reservations (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_isbn       VARCHAR(20) NOT NULL REFERENCES books(isbn) ON DELETE CASCADE,
    status          VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'fulfilled', 'cancelled', 'expired')),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expired_at      TIMESTAMP WITH TIME ZONE,
    fulfilled_at    TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_user_book_pending UNIQUE (user_id, book_isbn, status)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE scheduler_logs (
    id              SERIAL PRIMARY KEY,
    job_id          VARCHAR(100) NOT NULL,
    job_name        VARCHAR(100),
    status          VARCHAR(20) CHECK (status IN ('success', 'failed', 'running')),
    started_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    finished_at     TIMESTAMP WITH TIME ZONE,
    result          TEXT,
    error           TEXT
);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_books_updated_at BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_borrows_updated_at BEFORE UPDATE ON borrow_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE VIEW overdue_borrows AS
SELECT
    br.id,
    br.user_id,
    u.nickname as user_name,
    br.book_isbn,
    b.title as book_title,
    br.borrowed_at,
    br.due_date,
    EXTRACT(DAY FROM CURRENT_TIMESTAMP - br.due_date) as overdue_days
FROM borrow_records br
JOIN users u ON br.user_id = u.id
JOIN books b ON br.book_isbn = b.isbn
WHERE br.status = 'active' AND br.due_date < CURRENT_TIMESTAMP;

CREATE VIEW user_borrow_stats AS
SELECT
    u.id as user_id,
    u.nickname,
    COUNT(br.id) as total_borrows,
    COUNT(CASE WHEN br.status = 'active' THEN 1 END) as active_borrows,
    COUNT(CASE WHEN br.status = 'returned' THEN 1 END) as returned_count,
    COUNT(CASE WHEN br.status = 'active' AND br.due_date < CURRENT_TIMESTAMP THEN 1 END) as overdue_count
FROM users u
LEFT JOIN borrow_records br ON u.id = br.user_id
WHERE u.status = 'active'
GROUP BY u.id, u.nickname;

CREATE VIEW book_popularity AS
SELECT
    b.isbn,
    b.title,
    b.stock,
    COUNT(br.id) as borrow_count,
    COUNT(CASE WHEN br.status = 'active' THEN 1 END) as current_borrows
FROM books b
LEFT JOIN borrow_records br ON b.isbn = br.book_isbn
GROUP BY b.isbn, b.title, b.stock
ORDER BY borrow_count DESC;

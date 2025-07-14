-- ChatSphere 数据库初始化脚本
-- 此脚本在 PostgreSQL 容器启动时自动执行

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 设置时区
SET timezone = 'UTC';

-- 创建数据库用户（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'chatsphere') THEN
        CREATE ROLE chatsphere WITH LOGIN PASSWORD 'dev_password_123';
    END IF;
END
$$;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE chatsphere_dev TO chatsphere;
-- GRANT ALL PRIVILEGES ON DATABASE chatsphere_test TO chatsphere;
-- GRANT ALL PRIVILEGES ON DATABASE chatsphere_prod TO chatsphere;

-- 创建性能优化索引（这些将在应用启动时通过 Alembic 创建，这里仅作为参考）
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_room_created_at ON messages(room_id, created_at DESC);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_sender_created_at ON messages(sender_id, created_at DESC);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username_trgm ON users USING gin(username gin_trgm_ops);

-- 设置连接限制
ALTER ROLE chatsphere CONNECTION LIMIT 100;

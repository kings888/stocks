# 股市数据聚合平台部署文档

## 1. 系统环境要求

### 1.1 基础环境
- Python 3.8+
- PostgreSQL 12+
- Redis 6.0+
- Nginx 1.18+

### 1.2 系统配置
- 建议内存：4GB+
- CPU：2核+
- 磁盘空间：20GB+
- 操作系统：Ubuntu 20.04 LTS或CentOS 8+

## 2. 项目部署步骤

### 2.1 安装系统依赖
```bash
# Ubuntu
sudo apt update
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib redis-server nginx

# CentOS
sudo dnf install -y python38 python38-pip postgresql-server postgresql-contrib redis nginx
```

### 2.2 创建项目目录
```bash
mkdir -p /var/www/stocks
cd /var/www/stocks
```

### 2.3 克隆项目代码
```bash
git clone <项目仓库URL> .
```

### 2.4 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.5 安装项目依赖
```bash
pip install -r requirements.txt
```

### 2.6 配置环境变量
创建`.env`文件并配置以下环境变量：
```plaintext
DJANGO_SETTINGS_MODULE=stocks.settings
DJANGO_SECRET_KEY=<your-secret-key>
DATABASE_URL=postgres://user:password@localhost:5432/stocks
REDIS_URL=redis://localhost:6379/0
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### 2.7 数据库配置
```bash
# 创建数据库和用户
sudo -u postgres psql

CREATE DATABASE stocks;
CREATE USER stocks_user WITH PASSWORD 'your-password';
ALTER ROLE stocks_user SET client_encoding TO 'utf8';
ALTER ROLE stocks_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE stocks_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE stocks TO stocks_user;
\q

# 执行数据库迁移
python manage.py migrate
```

### 2.8 收集静态文件
```bash
python manage.py collectstatic --noinput
```

### 2.9 配置Gunicorn
创建`/etc/systemd/system/gunicorn_stocks.service`：
```ini
[Unit]
Description=gunicorn daemon for stocks project
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/stocks
EnvironmentFile=/var/www/stocks/.env
ExecStart=/var/www/stocks/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/stocks/stocks.sock \
          stocks.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 2.10 配置Nginx
创建`/etc/nginx/sites-available/stocks`：
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/stocks;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/stocks/stocks.sock;
    }
}
```

创建符号链接并重启Nginx：
```bash
sudo ln -s /etc/nginx/sites-available/stocks /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 2.11 配置Celery服务
创建`/etc/systemd/system/celery_stocks.service`：
```ini
[Unit]
Description=Celery Service for Stocks
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/stocks
EnvironmentFile=/var/www/stocks/.env
ExecStart=/var/www/stocks/venv/bin/celery -A stocks worker -l info

[Install]
WantedBy=multi-user.target
```

### 2.12 启动服务
```bash
# 启动Gunicorn
sudo systemctl start gunicorn_stocks
sudo systemctl enable gunicorn_stocks

# 启动Celery
sudo systemctl start celery_stocks
sudo systemctl enable celery_stocks
```

## 3. 系统监控建议

### 3.1 日志监控
- 配置日志轮转
- 使用ELK或Graylog进行日志聚合
- 设置关键错误告警

### 3.2 性能监控
- 使用Prometheus + Grafana监控系统指标
- 配置NewRelic或Datadog进行APM监控
- 监控关键API响应时间

### 3.3 安全建议
- 启用HTTPS（配置SSL证书）
- 定期更新系统和依赖包
- 配置防火墙规则
- 启用DDoS防护
- 定期备份数据

## 4. 故障排查

### 4.1 常见问题
1. 服务无法启动
   - 检查日志文件：`/var/log/nginx/error.log`
   - 检查Gunicorn日志
   - 验证环境变量配置

2. 数据库连接失败
   - 检查PostgreSQL服务状态
   - 验证数据库连接信息
   - 检查防火墙设置

3. 静态文件404
   - 确认collectstatic是否执行成功
   - 检查Nginx配置中的静态文件路径
   - 验证文件权限

### 4.2 性能优化
1. 数据库优化
   - 添加适当的索引
   - 优化慢查询
   - 配置连接池

2. 缓存优化
   - 合理使用Redis缓存
   - 配置页面缓存
   - 启用数据库查询缓存

3. 静态资源优化
   - 启用Gzip压缩
   - 配置浏览器缓存
   - 使用CDN加速

## 5. 维护指南

### 5.1 日常维护
1. 定期检查
   - 系统日志
   - 服务状态
   - 磁盘使用情况
   - 数据库备份

2. 更新维护
   - 系统包更新
   - 依赖包更新
   - 安全补丁安装

### 5.2 备份策略
1. 数据库备份
   ```bash
   # 创建备份脚本
   pg_dump -U stocks_user stocks > /backup/stocks_$(date +%Y%m%d).sql
   ```

2. 配置文件备份
   - 定期备份.env文件
   - 备份Nginx配置
   - 备份Systemd服务文件

### 5.3 扩展建议
1. 负载均衡
   - 配置多个Gunicorn工作进程
   - 使用Nginx进行负载均衡
   - 考虑使用容器化部署

2. 高可用性
   - 配置数据库主从复制
   - 使用Redis集群
   - 实现服务器冗余

   --TEXT
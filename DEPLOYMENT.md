# StudentSaaS 项目部署指南

本指南详细说明如何将 StudentSaaS 项目部署到阿里云 CentOS 服务器。

## 服务器信息

- **IP地址**: 123.56.84.70
- **用户名**: root
- **密码**: qweasd123Q
- **域名**: charonspace.asia
- **操作系统**: CentOS
- **已安装**: Python, MySQL

## 部署前准备

### 1. 本地环境检查

确保本地项目已准备就绪：

```bash
# 检查项目结构
tree /f /a "D:\StudentSaaS"

# 预期结构：
# D:\StudentSaaS
# ├── admin\backend\          # 总控制端后端
# │   ├── app\
# │   ├── requirements.txt
# │   ├── config.py
# │   ├── run.py
# │   └── .env.production
# ├── tenant\frontend\        # 租户端前端
# │   ├── src\
# │   ├── dist\               # 生产构建目录（需先构建）
# │   ├── package.json
# │   └── vite.config.js
# └── deploy.sh              # 部署脚本
```

### 2. 构建前端项目

如果尚未构建前端，请执行：

```bash
cd "D:\StudentSaaS\tenant\frontend"
npm run build
```

构建完成后，`dist` 目录将被创建。

### 3. 安装必要工具

在 Windows 上，需要安装以下工具：

1. **Git Bash** 或 **WSL2**（推荐）
2. **sshpass**（用于自动化密码登录）
   ```bash
   # 在 Git Bash 中安装 sshpass
   # 下载地址：https://sourceforge.net/projects/sshpass/
   # 或使用 chocolatey：choco install sshpass
   ```
3. **WinSCP**（可选，用于图形化文件传输）

## 部署步骤

### 步骤1：修改部署脚本配置

编辑 `deploy.sh` 脚本，确保以下变量正确：

```bash
SERVER_PASSWORD="qweasd123Q"           # 您的服务器密码
LOCAL_PROJECT_ROOT="/d/StudentSaaS"    # Git Bash 中的路径格式
```

### 步骤2：测试服务器连接

```bash
# 使用 sshpass 测试连接
sshpass -p "qweasd123Q" ssh -o StrictHostKeyChecking=no root@123.56.84.70 "echo '连接成功'"

# 或使用普通 SSH（需要手动输入密码）
ssh root@123.56.84.70
```

### 步骤3：执行部署脚本

```bash
# 在 Git Bash 中执行
export SSHPASS="qweasd123Q"
cd /d/StudentSaaS
bash deploy.sh
```

### 步骤4：手动配置（如果需要）

部署脚本会自动完成大部分工作，但以下项目可能需要手动配置：

#### 4.1 MySQL 数据库配置

登录 MySQL 并创建数据库：

```sql
mysql -u root -p
CREATE DATABASE IF NOT EXISTS student_saas_admin;
CREATE USER IF NOT EXISTS 'saas_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON student_saas_admin.* TO 'saas_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

然后更新 `.env.production` 文件中的数据库连接字符串。

#### 4.2 SSL 证书配置

1. 将 SSL 证书文件上传到服务器：
   ```bash
   sshpass -p "qweasd123Q" scp charonspace.asia.crt root@123.56.84.70:/etc/ssl/certs/
   sshpass -p "qweasd123Q" scp charonspace.asia.key root@123.56.84.70:/etc/ssl/private/
   ```

2. 或者使用 Let's Encrypt 免费证书：
   ```bash
   ssh root@123.56.84.70
   yum install -y certbot python3-certbot-nginx
   certbot --nginx -d charonspace.asia -d www.charonspace.asia
   ```

#### 4.3 防火墙配置

确保防火墙允许 HTTP(80) 和 HTTPS(443) 端口：

```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

### 步骤5：验证部署

1. **检查服务状态**：
   ```bash
   ssh root@123.56.84.70 "systemctl status student_saas_admin"
   ssh root@123.56.84.70 "systemctl status nginx"
   ```

2. **测试前端访问**：
   在浏览器中访问：
   - http://charonspace.asia（HTTP）
   - https://charonspace.asia（HTTPS，配置SSL后）

3. **测试后端 API**：
   ```bash
   curl http://charonspace.asia/api/health
   curl https://charonspace.asia/api/health
   ```

## 故障排除

### 常见问题

1. **SSH 连接失败**
   - 检查服务器IP和密码是否正确
   - 确保服务器防火墙允许SSH端口(22)
   - 尝试使用 `ssh -v root@123.56.84.70` 查看详细错误

2. **数据库连接错误**
   - 确认MySQL服务正在运行：`systemctl status mysqld`
   - 检查数据库用户权限
   - 验证连接字符串中的用户名和密码

3. **Nginx 配置错误**
   - 检查Nginx配置文件：`nginx -t`
   - 查看Nginx错误日志：`tail -f /var/log/nginx/error.log`
   - 确认Nginx服务已重启：`systemctl restart nginx`

4. **Python 依赖安装失败**
   - 确保已安装Python3和pip：`python3 --version`
   - 尝试升级pip：`pip install --upgrade pip`
   - 检查虚拟环境是否正确激活

5. **前端文件未正确服务**
   - 确认dist文件已复制到正确位置：`ls -la /var/www/student_saas/tenant/`
   - 检查Nginx配置中的root目录设置
   - 确认文件权限：`chown -R nginx:nginx /var/www/student_saas`

### 日志文件位置

- **后端应用日志**：`/var/log/student_saas_admin.log`
- **Nginx 访问日志**：`/var/log/nginx/access.log`
- **Nginx 错误日志**：`/var/log/nginx/error.log`
- **系统日志**：`journalctl -u student_saas_admin`

## 维护和更新

### 更新前端

1. 本地重新构建前端：
   ```bash
   cd "D:\StudentSaaS\tenant\frontend"
npm run build
   ```

2. 重新部署前端文件：
   ```bash
   sshpass -p "qweasd123Q" scp -r "D:\StudentSaaS\tenant\frontend\dist\*" root@123.56.84.70:/var/www/student_saas/tenant/
   ```

3. 重启Nginx：
   ```bash
   ssh root@123.56.84.70 "systemctl restart nginx"
   ```

### 更新后端

1. 更新代码后，重新复制到服务器：
   ```bash
   # 使用部署脚本或手动复制
   bash deploy.sh
   ```

2. 重启后端服务：
   ```bash
   ssh root@123.56.84.70 "systemctl restart student_saas_admin"
   ```

### 备份数据库

```bash
# 在服务器上执行
mysqldump -u root -p student_saas_admin > backup_$(date +%Y%m%d).sql
```

## 安全建议

1. **修改默认密码**：
   - 修改服务器root密码
   - 修改MySQL root密码
   - 修改应用中的SECRET_KEY和JWT_SECRET_KEY

2. **使用SSH密钥认证**：
   ```bash
   # 生成SSH密钥
   ssh-keygen -t rsa -b 4096
   
   # 将公钥复制到服务器
   ssh-copy-id root@123.56.84.70
   
   # 禁用密码登录（谨慎操作）
   # 编辑 /etc/ssh/sshd_config
   # PasswordAuthentication no
   # 然后重启SSH服务
   ```

3. **配置防火墙**：
   - 只开放必要的端口（80, 443, 22）
   - 考虑使用fail2ban防止暴力破解

4. **定期更新系统**：
   ```bash
   yum update -y
   yum upgrade -y
   ```

## 联系方式

如果在部署过程中遇到问题，请检查日志文件或联系系统管理员。

---

*最后更新：2024年*  
*文档版本：1.0*
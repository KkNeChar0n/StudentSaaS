#!/bin/bash
# StudentSaaS 项目部署脚本 - CentOS 阿里云服务器
# 目标服务器: 123.56.84.70 (root)
# 域名: charonspace.asia

set -e  # 出错时退出

# ============ 配置变量 ============
SERVER_IP="123.56.84.70"
SERVER_USER="root"
SERVER_PASSWORD="qweasd123Q"  # 注意：在生产环境中建议使用SSH密钥
DOMAIN="charonspace.asia"

# 本地项目路径
LOCAL_PROJECT_ROOT="/mnt/d/StudentSaaS"  # 根据实际Windows路径调整，或使用相对路径
LOCAL_TENANT_FRONTEND="${LOCAL_PROJECT_ROOT}/tenant/frontend"
LOCAL_ADMIN_BACKEND="${LOCAL_PROJECT_ROOT}/admin/backend"

# 服务器部署路径
SERVER_DEPLOY_ROOT="/opt/student_saas"
SERVER_TENANT_FRONTEND="${SERVER_DEPLOY_ROOT}/tenant/frontend"
SERVER_ADMIN_BACKEND="${SERVER_DEPLOY_ROOT}/admin/backend"
SERVER_NGINX_ROOT="/var/www/student-saas"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============ 辅助函数 ============
function log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

function log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

function log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

function run_ssh() {
    # 使用sshpass传递密码（需要安装sshpass）
    sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_IP}" "$1"
}

function run_scp() {
    # 复制文件到服务器
    sshpass -p "${SERVER_PASSWORD}" scp -o StrictHostKeyChecking=no -r "$1" "${SERVER_USER}@${SERVER_IP}:$2"
}

# ============ 主部署流程 ============
function main() {
    log_info "开始部署 StudentSaaS 项目到 ${SERVER_IP}"
    
    # 步骤1: 检查并创建服务器目录结构
    setup_server_directories
    
    # 步骤2: 部署租户端前端
    deploy_tenant_frontend
    
    # 步骤3: 部署总控制端后端
    deploy_admin_backend
    
    # 步骤4: 配置服务器环境
    setup_server_environment
    
    # 步骤5: 配置Nginx反向代理
    setup_nginx
    
    # 步骤6: 配置SSL证书（需要提前准备证书文件）
    setup_ssl
    
    # 步骤7: 启动服务
    start_services
    
    log_info "部署完成！"
    log_info "前端访问: https://${DOMAIN}"
    log_info "后端API: https://${DOMAIN}/api"
}

# ============ 具体步骤函数 ============
function setup_server_directories() {
    log_info "步骤1: 设置服务器目录结构"
    
    local dirs=(
        "${SERVER_DEPLOY_ROOT}"
        "${SERVER_TENANT_FRONTEND}"
        "${SERVER_ADMIN_BACKEND}"
        "${SERVER_NGINX_ROOT}"
        "${SERVER_NGINX_ROOT}/tenant"
        "${SERVER_NGINX_ROOT}/admin"
        "/var/log/student_saas"
    )
    
    for dir in "${dirs[@]}"; do
        run_ssh "mkdir -p ${dir}"
    done
}

function deploy_tenant_frontend() {
    log_info "步骤2: 部署租户端前端"
    
    # 检查服务器上是否已有从GitHub Actions复制过来的dist目录
    if run_ssh "[ -d /var/www/student-saas/tenant-frontend ]"; then
        log_info "使用GitHub Actions已复制的dist目录"
        # 将tenant-frontend目录中的内容移动到tenant目录
        run_ssh "mv /var/www/student-saas/tenant-frontend/* ${SERVER_NGINX_ROOT}/tenant/ 2>/dev/null || true"
        run_ssh "rmdir /var/www/student-saas/tenant-frontend 2>/dev/null || true"
    else
        # 否则，检查本地dist目录（适用于本地运行部署脚本的情况）
        if [ ! -d "${LOCAL_TENANT_FRONTEND}/dist" ]; then
            log_error "本地dist目录不存在，请先运行 'npm run build'"
            exit 1
        fi
        # 复制构建文件到服务器
        log_info "复制前端构建文件..."
        run_scp "${LOCAL_TENANT_FRONTEND}/dist/*" "${SERVER_NGINX_ROOT}/tenant/"
    fi
    
    # 设置权限
    run_ssh "chown -R nginx:nginx ${SERVER_NGINX_ROOT}/tenant"
    run_ssh "chmod -R 755 ${SERVER_NGINX_ROOT}/tenant"
}

function deploy_admin_backend() {
    log_info "步骤3: 部署总控制端后端"
    
    # 创建临时目录并复制文件
    local temp_dir="/tmp/student_saas_backend_$(date +%s)"
    mkdir -p "${temp_dir}"
    
    # 复制后端文件（排除不需要的文件）
    cp -r "${LOCAL_ADMIN_BACKEND}/"* "${temp_dir}/" 2>/dev/null || true
    
    # 清理不必要的文件
    rm -rf "${temp_dir}/__pycache__" "${temp_dir}/.git" "${temp_dir}/venv" "${temp_dir}/dev.db" 2>/dev/null || true
    
    # 复制到服务器
    log_info "复制后端文件..."
    run_scp "${temp_dir}" "${SERVER_ADMIN_BACKEND}"
    
    # 清理临时目录
    rm -rf "${temp_dir}"
    
    # 在服务器上设置Python虚拟环境
    log_info "设置Python虚拟环境..."
    run_ssh "cd ${SERVER_ADMIN_BACKEND} && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
}

function setup_server_environment() {
    log_info "步骤4: 配置服务器环境"
    
    # 安装必要软件包
    run_ssh "yum update -y && yum install -y epel-release"
    run_ssh "yum install -y nginx python3 python3-devel mysql-devel gcc firewalld"
    
    # 安装Node.js（用于前端构建，如果需要）
    run_ssh "curl -sL https://rpm.nodesource.com/setup_18.x | bash - && yum install -y nodejs"
    
    # 启动并启用防火墙
    run_ssh "systemctl start firewalld && systemctl enable firewalld"
    run_ssh "firewall-cmd --permanent --add-service=http && firewall-cmd --permanent --add-service=https && firewall-cmd --reload"
    
    # 设置MySQL（如果尚未配置）
    log_warn "请确保MySQL已安装并运行，数据库 'student_saas_admin' 已创建"
    log_warn "运行以下命令配置MySQL："
    echo "mysql -u root -p"
    echo "CREATE DATABASE IF NOT EXISTS student_saas_admin;"
    echo "CREATE USER IF NOT EXISTS 'saas_user'@'localhost' IDENTIFIED BY 'your_password';"
    echo "GRANT ALL PRIVILEGES ON student_saas_admin.* TO 'saas_user'@'localhost';"
    echo "FLUSH PRIVILEGES;"
}

function setup_nginx() {
    log_info "步骤5: 配置Nginx反向代理"
    
    # 创建Nginx配置文件
    local nginx_conf="/tmp/student_saas_nginx.conf"
    cat > "${nginx_conf}" << EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};
    root ${SERVER_NGINX_ROOT}/tenant;
    index index.html;

    # 前端静态文件
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 静态文件缓存
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    # 复制到服务器
    run_scp "${nginx_conf}" "${SERVER_USER}@${SERVER_IP}:/etc/nginx/conf.d/student_saas.conf"
    rm -f "${nginx_conf}"
    
    # 测试并重载Nginx配置
    run_ssh "nginx -t && systemctl restart nginx && systemctl enable nginx"
}

function setup_ssl() {
    log_info "步骤6: 配置SSL证书（需要手动步骤）"
    
    log_warn "SSL证书配置需要手动完成："
    echo "1. 将SSL证书文件上传到服务器："
    echo "   scp charonspace.asia.crt ${SERVER_USER}@${SERVER_IP}:/etc/ssl/certs/"
    echo "   scp charonspace.asia.key ${SERVER_USER}@${SERVER_IP}:/etc/ssl/private/"
    echo "2. 修改Nginx配置启用HTTPS"
    echo "3. 使用Let's Encrypt免费证书："
    echo "   yum install -y certbot python3-certbot-nginx"
    echo "   certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
}

function start_services() {
    log_info "步骤7: 启动服务"
    
    # 创建系统服务文件
    local service_conf="/tmp/student_saas_admin.service"
    cat > "${service_conf}" << EOF
[Unit]
Description=StudentSaaS Admin Backend
After=network.target

[Service]
Type=simple
User=nginx
Group=nginx
WorkingDirectory=${SERVER_ADMIN_BACKEND}
Environment="PATH=${SERVER_ADMIN_BACKEND}/venv/bin"
EnvironmentFile=${SERVER_ADMIN_BACKEND}/.env.production
ExecStart=${SERVER_ADMIN_BACKEND}/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 run:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 复制到服务器并启用服务
    run_scp "${service_conf}" "${SERVER_USER}@${SERVER_IP}:/etc/systemd/system/student_saas_admin.service"
    rm -f "${service_conf}"
    
    run_ssh "systemctl daemon-reload && systemctl start student_saas_admin && systemctl enable student_saas_admin"
    
    # 检查服务状态
    run_ssh "systemctl status student_saas_admin --no-pager"
    run_ssh "systemctl status nginx --no-pager"
}

# ============ 执行主函数 ============
if [[ "$1" == "--help" ]]; then
    echo "使用方法："
    echo "  ./deploy.sh          执行完整部署"
    echo "  ./deploy.sh --help   显示帮助信息"
    echo ""
    echo "注意："
    echo "1. 确保本地已安装 sshpass: apt-get install sshpass 或 brew install hudochenkov/sshpass/sshpass"
    echo "2. 确保前端已构建: cd tenant/frontend && npm run build"
    echo "3. 修改脚本中的数据库密码和其他敏感信息"
    exit 0
fi

# 检查必要工具
if ! command -v sshpass &> /dev/null; then
    log_error "请先安装 sshpass"
    log_warn "Ubuntu/Debian: sudo apt-get install sshpass"
    log_warn "macOS: brew install hudochenkov/sshpass/sshpass"
    exit 1
fi

main
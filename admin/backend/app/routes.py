from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from app import db
from app.models import User, Tenant, Role, Permission, SubscriptionPlan
import re

# 创建蓝图
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
tenant_bp = Blueprint('tenant', __name__, url_prefix='/api/tenants')
user_bp = Blueprint('user', __name__, url_prefix='/api/users')
role_bp = Blueprint('role', __name__, url_prefix='/api/roles')
plan_bp = Blueprint('plan', __name__, url_prefix='/api/plans')

# 辅助函数
def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# 主路由
@main_bp.route('/')
def index():
    return jsonify({
        'message': 'Student SaaS Admin API',
        'version': '1.0.0',
        'status': 'running'
    })

@main_bp.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })

# 认证路由
@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data:
        return jsonify({'message': '缺少请求数据'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400
    
    # 查找用户
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': '用户名或密码错误'}), 401
    
    if not user.check_password(password):
        return jsonify({'message': '用户名或密码错误'}), 401
    
    if not user.is_active:
        return jsonify({'message': '用户已被禁用'}), 401
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # 创建令牌
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'message': '登录成功',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'is_superuser': user.is_superuser,
            'tenant_id': user.tenant_id
        }
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    # 在实际应用中，可以将令牌加入黑名单
    return jsonify({'message': '登出成功'}), 200

# 租户管理路由
@tenant_bp.route('/', methods=['GET'])
@jwt_required()
def get_tenants():
    """获取租户列表"""
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    query = Tenant.query
    
    if search:
        query = query.filter(Tenant.name.ilike(f'%{search}%'))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    tenants = pagination.items
    
    return jsonify({
        'tenants': [{
            'id': tenant.id,
            'name': tenant.name,
            'subdomain': tenant.subdomain,
            'contact_email': tenant.contact_email,
            'contact_phone': tenant.contact_phone,
            'max_users': tenant.max_users,
            'is_active': tenant.is_active,
            'subscription_plan': tenant.subscription_plan,
            'subscription_expires': tenant.subscription_expires.isoformat() if tenant.subscription_expires else None,
            'created_at': tenant.created_at.isoformat() + 'Z'
        } for tenant in tenants],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@tenant_bp.route('/<int:tenant_id>', methods=['GET'])
@jwt_required()
def get_tenant(tenant_id):
    """获取单个租户信息"""
    tenant = Tenant.query.get_or_404(tenant_id)
    return jsonify({
        'id': tenant.id,
        'name': tenant.name,
        'subdomain': tenant.subdomain,
        'contact_email': tenant.contact_email,
        'contact_phone': tenant.contact_phone,
        'max_users': tenant.max_users,
        'is_active': tenant.is_active,
        'subscription_plan': tenant.subscription_plan,
        'subscription_expires': tenant.subscription_expires.isoformat() if tenant.subscription_expires else None,
        'created_at': tenant.created_at.isoformat() + 'Z',
        'updated_at': tenant.updated_at.isoformat() + 'Z'
    }), 200

@tenant_bp.route('/', methods=['POST'])
@jwt_required()
def create_tenant():
    """创建新租户"""
    data = request.get_json()
    if not data:
        return jsonify({'message': '缺少请求数据'}), 400
    
    required_fields = ['name', 'subdomain', 'contact_email']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'缺少必填字段: {field}'}), 400
    
    # 验证邮箱
    if not validate_email(data['contact_email']):
        return jsonify({'message': '邮箱格式不正确'}), 400
    
    # 检查租户名和子域名是否已存在
    if Tenant.query.filter_by(name=data['name']).first():
        return jsonify({'message': '租户名称已存在'}), 400
    if Tenant.query.filter_by(subdomain=data['subdomain']).first():
        return jsonify({'message': '子域名已存在'}), 400
    
    tenant = Tenant(
        name=data['name'],
        subdomain=data['subdomain'],
        contact_email=data['contact_email'],
        contact_phone=data.get('contact_phone'),
        max_users=data.get('max_users', 10),
        is_active=data.get('is_active', True),
        subscription_plan=data.get('subscription_plan', 'basic'),
        subscription_expires=data.get('subscription_expires')
    )
    
    db.session.add(tenant)
    db.session.commit()
    
    return jsonify({
        'message': '租户创建成功',
        'tenant_id': tenant.id
    }), 201

@tenant_bp.route('/<int:tenant_id>', methods=['PUT'])
@jwt_required()
def update_tenant(tenant_id):
    """更新租户信息"""
    tenant = Tenant.query.get_or_404(tenant_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'message': '缺少请求数据'}), 400
    
    # 更新字段
    if 'name' in data and data['name'] != tenant.name:
        if Tenant.query.filter_by(name=data['name']).first():
            return jsonify({'message': '租户名称已存在'}), 400
        tenant.name = data['name']
    
    if 'subdomain' in data and data['subdomain'] != tenant.subdomain:
        if Tenant.query.filter_by(subdomain=data['subdomain']).first():
            return jsonify({'message': '子域名已存在'}), 400
        tenant.subdomain = data['subdomain']
    
    if 'contact_email' in data:
        if not validate_email(data['contact_email']):
            return jsonify({'message': '邮箱格式不正确'}), 400
        tenant.contact_email = data['contact_email']
    
    if 'contact_phone' in data:
        tenant.contact_phone = data['contact_phone']
    
    if 'max_users' in data:
        tenant.max_users = data['max_users']
    
    if 'is_active' in data:
        tenant.is_active = data['is_active']
    
    if 'subscription_plan' in data:
        tenant.subscription_plan = data['subscription_plan']
    
    if 'subscription_expires' in data:
        tenant.subscription_expires = data['subscription_expires']
    
    db.session.commit()
    
    return jsonify({'message': '租户更新成功'}), 200

@tenant_bp.route('/<int:tenant_id>', methods=['DELETE'])
@jwt_required()
def delete_tenant(tenant_id):
    """删除租户"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    # 检查是否有用户关联
    if tenant.users.count() > 0:
        return jsonify({'message': '该租户下存在用户，无法删除'}), 400
    
    db.session.delete(tenant)
    db.session.commit()
    
    return jsonify({'message': '租户删除成功'}), 200

@tenant_bp.route('/<int:tenant_id>/activate', methods=['POST'])
@jwt_required()
def activate_tenant(tenant_id):
    """激活租户"""
    tenant = Tenant.query.get_or_404(tenant_id)
    tenant.is_active = True
    db.session.commit()
    return jsonify({'message': '租户已激活'}), 200

@tenant_bp.route('/<int:tenant_id>/deactivate', methods=['POST'])
@jwt_required()
def deactivate_tenant(tenant_id):
    """停用租户"""
    tenant = Tenant.query.get_or_404(tenant_id)
    tenant.is_active = False
    db.session.commit()
    return jsonify({'message': '租户已停用'}), 200

# 用户管理路由 - 基础版本
@user_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = User.query
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    
    return jsonify({
        'users': [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'is_active': user.is_active,
            'is_superuser': user.is_superuser,
            'tenant_id': user.tenant_id,
            'last_login': user.last_login.isoformat() + 'Z' if user.last_login else None
        } for user in users],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

# 套餐管理路由 - 基础版本
@plan_bp.route('/', methods=['GET'])
def get_plans():
    """获取套餐列表"""
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    return jsonify({
        'plans': [{
            'id': plan.id,
            'name': plan.name,
            'code': plan.code,
            'price_monthly': plan.price_monthly,
            'price_yearly': plan.price_yearly,
            'max_users': plan.max_users,
            'max_storage': plan.max_storage,
            'features': plan.features
        } for plan in plans]
    }), 200

# 注册蓝图函数
def register_routes(app):
    """注册所有蓝图到应用"""
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tenant_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(role_bp)
    app.register_blueprint(plan_bp)

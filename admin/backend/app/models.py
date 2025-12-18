from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Tenant(db.Model):
    """租户模型"""
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    subdomain = db.Column(db.String(64), unique=True, nullable=False)
    contact_email = db.Column(db.String(128), nullable=False)
    contact_phone = db.Column(db.String(32))
    max_users = db.Column(db.Integer, default=10)
    is_active = db.Column(db.Boolean, default=True)
    subscription_plan = db.Column(db.String(64), default='basic')
    subscription_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = db.relationship('User', backref='tenant', lazy='dynamic')

    def __repr__(self):
        return f'<Tenant {self.name}>'


class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    is_active = db.Column(db.Boolean, default=True)
    is_superuser = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    permissions = db.relationship('Permission', secondary='role_permissions', backref=db.backref('roles', lazy='dynamic'))
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'


class Permission(db.Model):
    """权限模型"""
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64))
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Permission {self.code}>'


# 角色权限关联表
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)


class SubscriptionPlan(db.Model):
    """套餐模型"""
    __tablename__ = 'subscription_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    code = db.Column(db.String(64), unique=True, nullable=False)
    price_monthly = db.Column(db.Float, nullable=False)
    price_yearly = db.Column(db.Float)
    max_users = db.Column(db.Integer, nullable=False)
    max_storage = db.Column(db.Integer, nullable=False)  # MB
    features = db.Column(db.JSON)  # 存储特性列表
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenants = db.relationship('Tenant', backref='plan', lazy='dynamic')

    def __repr__(self):
        return f'<SubscriptionPlan {self.name}>'
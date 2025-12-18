from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()


def create_app(config_name='default'):
    """
    应用工厂函数
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    jwt.init_app(app)

    # 注册蓝图
    from app.routes import main_bp, auth_bp, tenant_bp, user_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(tenant_bp, url_prefix='/tenants')
    app.register_blueprint(user_bp, url_prefix='/users')

    # 创建数据库表（如果不存在）
    with app.app_context():
        db.create_all()

    return app
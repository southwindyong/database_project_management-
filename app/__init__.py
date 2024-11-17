from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from app.models import User
        # 创建默认管理员
        if not User.query.filter_by(role="管理员").first():
            admin = User(
                username="admin",
                email="admin@example.com",
                first_name="Default",
                last_name="Admin",
                role="管理员",
                status="激活"
            )
            admin.set_password("adminpassword")
            db.session.add(admin)
            db.session.commit()

    # 注册蓝图
    from app.routes import main_bp
    from app.auth_routes import auth_bp
    app.register_blueprint(auth_bp)  # 默认访问 auth 路由
    app.register_blueprint(main_bp, url_prefix='/main')  # 登录后访问 main 路由

    return app

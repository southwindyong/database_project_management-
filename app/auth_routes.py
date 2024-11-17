from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import User
from sqlalchemy.exc import IntegrityError

@auth_bp.route('/')
def home():
    # 如果用户已登录，重定向到主页面
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    # 否则，显示欢迎页面
    return render_template('welcome.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if user.status == "激活":
                session['user_id'] = user.user_id
                session['username'] = user.username
                session['role'] = user.role
                return redirect(url_for('main.index'))  # 登录后跳转到主页
            else:
                flash("您的账户尚未被管理员激活，请稍后再试。", "login_error")
                return redirect(url_for('auth.login'))
        
        flash('用户名或密码错误，请重试。', "login_error")
        return redirect(url_for('auth.login'))  # 错误时跳转回登录页面
    
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        # 验证必填字段
        if not all([username, email, password, first_name, last_name]):
            flash("所有字段都必须填写", "register_error")
            return redirect(url_for('auth.register'))

        # 尝试插入新用户，捕获唯一性错误（email重复）
        try:
            new_user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role="普通用户",
                status="待审核"
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()

            flash("注册成功，请等待管理员激活您的账户。", "registration")
            return redirect(url_for('auth.login'))
        
        except IntegrityError as e:
            db.session.rollback()  # 回滚事务
            if 'users_email_key' in str(e.orig):  # 判断是否是email重复错误
                flash("该电子邮件已被注册，请使用其他电子邮件地址。", "register_error")
            elif 'users_username_key' in str(e.orig):  # 判断是否是username重复错误
                flash("该用户名已被注册，请使用其他用户名。", "register_error")
            else:
                flash("注册时发生错误，请稍后再试。", "register_error")
            return redirect(url_for('auth.register'))
    
    return render_template('register.html')


@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class Project(db.Model):
    __tablename__ = 'projects'

    project_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(50), nullable=False)
    budget = db.Column(db.Float, nullable=False)
    is_public = db.Column(db.Boolean, default=False, nullable=False)  # 新增公开选项

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    members = db.relationship('ProjectMember', backref='project', lazy=True)
    approvals = db.relationship('Approval', backref='project', lazy=True)
    documents = db.relationship('ProjectDocument', backref='project', lazy=True)


# 项目成员表
class ProjectMember(db.Model):
    __tablename__ = 'project_members'
    
    member_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    join_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    leave_date = db.Column(db.DateTime, nullable=True)
    
    # 添加与 User 模型的关系
    user = db.relationship('User', backref='project_members', lazy=True)


# 用户表
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="普通用户")  # 默认角色为普通用户
    status = db.Column(db.String(20), nullable=False, default="待审核")  # 初始状态为“待审核”
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 设置和检查密码
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 审批事项表
class Approval(db.Model):
    __tablename__ = 'approvals'
    
    approval_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=False)
    request_type = db.Column(db.String(50), nullable=False)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    status = db.Column(db.String(20), default='待审批')
    approval_date = db.Column(db.DateTime, nullable=True)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系定义
    requester = db.relationship('User', foreign_keys=[requested_by], backref='requested_approvals')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_approvals')


# 项目文档表
class ProjectDocument(db.Model):
    __tablename__ = 'project_documents'
    document_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=False)
    document_name = db.Column(db.String(100), nullable=False)
    document_description = db.Column(db.String(255), nullable=True)
    document_type = db.Column(db.String(50), nullable=False)
    document_link = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    access_level = db.Column(db.String(50), nullable=False)
    tags = db.Column(db.String(255), nullable=True)

class ApprovalHistory(db.Model):
    __tablename__ = 'approval_history'

    history_id = db.Column(db.Integer, primary_key=True)
    approval_id = db.Column(db.Integer, db.ForeignKey('approvals.approval_id'), nullable=False)  # 外键关联到 Approval 表
    status = db.Column(db.String(50), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # 外键关联到 User 表
    approval_date = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.Column(db.Text)

    # 反向关系
    approval = db.relationship('Approval', backref=db.backref('history', lazy=True))  # ApprovalHistory 与 Approval 之间的关系
    user = db.relationship('User', backref=db.backref('approval_histories', lazy=True))  # ApprovalHistory 与 User 之间的关系

    def __repr__(self):
        return f"<ApprovalHistory {self.approval_id} - {self.status}>"
    

class Notification(db.Model):
    __tablename__ = 'notifications'

    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # 外键关联到 User
    message = db.Column(db.String(255), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    related_id = db.Column(db.Integer, nullable=True)

    # 定义与 User 模型的关系
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f'<Notification {self.notification_id}, User {self.user_id}>'
    

class Message(db.Model):
    message_id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # 外键引用改为 'users.user_id'
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # 外键引用改为 'users.user_id'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

    def __repr__(self):
        return f'<Message {self.message_id} from {self.sender.username} to {self.receiver.username}>'
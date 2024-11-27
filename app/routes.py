from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app import db
from app.models import Project, User, ProjectMember, Approval,Notification,ApprovalHistory,Message
from datetime import datetime

main_bp = Blueprint('main', __name__)

def send_notification(user_id, message, notification_type, related_id=None):
    notification = Notification(
        user_id=user_id,
        message=message,
        notification_type=notification_type,
        related_id=related_id
    )
    db.session.add(notification)
    db.session.commit()

@main_bp.route('/index', methods=['GET'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    role = session.get('role', '')

    # 获取所有项目列表
    if role == '管理员':
        all_projects = Project.query.all()
        user_projects = Project.query.join(ProjectMember).filter(ProjectMember.user_id == user_id).all()
    else:
        all_projects = Project.query.filter_by(is_public=True).all()
        user_projects = Project.query.join(ProjectMember).filter(ProjectMember.user_id == user_id).all()

    # 查询待审批事项和已提交事项
    pending_approvals = Approval.query.filter_by(approved_by=user_id, status='待审批').all()
    submitted_approvals = Approval.query.filter_by(requested_by=user_id).all()

    # 获取用户的通知列表
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

    # 获取当前用户的最近10条消息
    recent_messages = Message.query.filter_by(receiver_id=user_id).order_by(Message.created_at.desc()).limit(10).all()

    return render_template('index.html', 
                           role=role, 
                           all_projects=all_projects, 
                           user_projects=user_projects,
                           pending_approvals=pending_approvals, 
                           submitted_approvals=submitted_approvals,
                           notifications=notifications,
                           recent_messages=recent_messages)  # 传递最近10条消息数据



@main_bp.route('/projects/create', methods=['GET', 'POST'])
def create_project():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        # 获取表单数据
        project_name = request.form['project_name']
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        status = request.form['status']
        priority = request.form['priority']
        budget = request.form['budget']
        is_public = 'is_public' in request.form  # 公开选项
        
        # 表单验证：检查必填字段是否为空
        if not all([project_name, description, start_date, end_date, status, priority, budget]):
            flash("所有字段都必须填写", "create_project_error")
            return redirect(url_for('main.create_project'))

        try:
            # 预算必须是数字
            budget = float(budget)
        except ValueError:
            flash("预算必须是一个有效的数字", "create_project_error")
            return redirect(url_for('main.create_project'))

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            flash("日期格式错误，请使用 YYYY-MM-DD 格式", "create_project_error")
            return redirect(url_for('main.create_project'))

        # 创建新项目
        new_project = Project(
            project_name=project_name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
            priority=priority,
            budget=budget,
            is_public=is_public
        )
        
        # 提交项目数据以生成 project_id
        db.session.add(new_project)
        db.session.commit()

        # 获取当前用户的 ID
        user_id = session['user_id']

        # 创建项目成员记录，将创建者添加到项目成员中
        new_member = ProjectMember(
            project_id=new_project.project_id,  # 获取提交后生成的 project_id
            user_id=user_id,
            role='项目负责人',  # 设置当前用户的角色为项目负责人
            join_date=datetime.utcnow()
        )
        
        # 将项目成员信息添加到数据库
        db.session.add(new_member)
        db.session.commit()

        flash("项目创建成功！并已将您作为项目负责人加入！", "project_create_success")
        return redirect(url_for('main.index'))

    return render_template('create_project.html')


@main_bp.route('/projects/<int:project_id>', methods=['GET', 'POST'])
def project_detail(project_id):
    project = Project.query.filter_by(project_id=project_id).first()
    if not project:
        flash('项目不存在', 'error')
        return redirect(url_for('main.index'))

    project_members = ProjectMember.query.filter_by(project_id=project_id).all()
    is_member = any(member.user_id == session['user_id'] for member in project_members)
    is_admin = session.get('role') == '管理员'
    
    # 获取当前项目的所有成员的 user_id
    existing_member_ids = [member.user_id for member in project_members]
    # 判断当前用户是否是项目负责人
    is_project_leader = any(member.user_id == session['user_id'] and member.role == '项目负责人' for member in project_members)

    # 获取所有用户
    all_users = User.query.all()

    # 过滤出当前项目未加入的用户
    available_users = [user for user in all_users if user.user_id not in existing_member_ids]

    # 用户是否有权限查看项目（成员、管理员、或项目负责人）
    if not is_member and not is_admin and not is_project_leader:
        flash('您没有权限查看此项目', 'error')
        return redirect(url_for('main.index'))

    # 查询与该项目相关的所有审批事项
    approvals = Approval.query.filter_by(project_id=project_id).all()

    # 处理添加成员的操作（POST 请求）
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        role = request.form.get('role')

        # 检查用户是否存在
        user = User.query.filter_by(user_id=user_id).first()
        if user and user.user_id not in existing_member_ids:
            # 添加成员
            new_member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
            db.session.add(new_member)
            db.session.commit()
            flash('项目成员添加成功', 'success')
        else:
            flash('无效的用户或用户已是项目成员', 'error')
        
        return redirect(url_for('main.project_detail', project_id=project_id))

    return render_template('project_detail.html', project=project, project_members=project_members,
                           is_member=is_member, is_admin=is_admin, is_project_leader=is_project_leader,
                           approvals=approvals, available_users=available_users)


@main_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    project = Project.query.get_or_404(project_id)

    # 获取项目的所有成员
    project_members = ProjectMember.query.filter_by(project_id=project_id).all()
    
    # 判断当前用户是否是项目成员，或者是管理员
    is_member = any(member.user_id == session['user_id'] for member in project_members)
    if not is_member and session['role'] != '管理员':
        return "无权限编辑此项目", 403

    if request.method == 'POST':
        # 获取表单数据
        project_name = request.form['project_name']
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        status = request.form['status']
        priority = request.form['priority']
        budget = request.form['budget']
        is_public = 'is_public' in request.form  # 公开选项

        # 表单验证
        if not all([project_name, description, start_date, end_date, status, priority, budget]):
            flash("所有字段都必须填写", "create_project_error")
            return redirect(url_for('main.edit_project', project_id=project_id))

        try:
            budget = float(budget)
        except ValueError:
            flash("预算必须是一个有效的数字", "create_project_error")
            return redirect(url_for('main.edit_project', project_id=project_id))

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            flash("日期格式错误，请使用 YYYY-MM-DD 格式", "create_project_error")
            return redirect(url_for('main.edit_project', project_id=project_id))

        # 更新项目数据
        project.project_name = project_name
        project.description = description
        project.start_date = start_date
        project.end_date = end_date
        project.status = status
        project.priority = priority
        project.budget = budget
        project.is_public = is_public

        db.session.commit()

        # 发送通知给所有项目成员
        for member in project_members:
            send_notification(
                member.user_id, 
                f"项目 {project_name} 已更新。",
                "项目信息变动",
                project_id
            )

        flash("项目更新成功", "success")
        return redirect(url_for('main.project_detail', project_id=project_id))

    return render_template('edit_project.html', project=project)


@main_bp.route('/projects/<int:project_id>/request_approval', methods=['GET', 'POST'])
def request_approval(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # 获取项目成员列表
    project_members = db.session.query(User).join(ProjectMember).filter(ProjectMember.project_id == project_id).all()

    if request.method == 'POST':
        # 检查是否选择了“其他”
        request_type = request.form['request_type']
        if request_type == "其他":
            request_type = request.form['custom_request_type']  # 使用自定义类型

        comments = request.form.get('comments', '')
        approved_by = request.form['approved_by']  # 选择的审批人 ID

        # 创建新审批记录
        new_approval = Approval(
            project_id=project_id,
            request_type=request_type,
            requested_by=session['user_id'],
            approved_by=approved_by,
            comments=comments,
            status='待审批',
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_approval)
        db.session.commit()

        # 发送通知给审批人
        send_notification(
            approved_by,  # 通知给审批人
            f"您有一条待审批的请求，来自项目 {project_id} 的审批请求。",
            "待审批",
            new_approval.approval_id  # 将审批 ID 作为通知的相关 ID
        )

        # 发送通知给请求人
        send_notification(
            session['user_id'],  # 通知给请求审批的用户
            f"您的审批请求已提交，等待审批人处理。",
            "提交的审批",
            new_approval.approval_id  # 将审批 ID 作为通知的相关 ID
        )

        flash("审批请求成功，等待审批人处理", "approval_success")
        return redirect(url_for('main.project_detail', project_id=project_id))

    return render_template('request_approval.html', project_id=project_id, project_members=project_members)



@main_bp.route('/projects/<int:project_id>/approvals', methods=['GET'])
def view_approvals(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # 获取当前项目的所有审批记录
    approvals = Approval.query.filter_by(project_id=project_id).all()
    return render_template('view_approvals.html', approvals=approvals, project_id=project_id)

@main_bp.route('/approvals/<int:approval_id>/process', methods=['POST'])
def process_approval(approval_id):
    # 确保用户是管理员
    if 'user_id' not in session or session.get('role') != '管理员':
        return "无权限操作", 403

    # 获取待处理的审批记录
    approval = Approval.query.get_or_404(approval_id)
    status = request.form['status']
    comments = request.form.get('comments', '')

    # 检查审批状态是否有效
    if status not in ['已批准', '已拒绝']:
        flash("无效的审批状态", "error")
        return redirect(url_for('main.view_approvals', project_id=approval.project_id))

    # 更新审批记录的状态
    approval.status = status
    approval.comments = comments
    approval.approved_by = session['user_id']
    approval.approval_date = datetime.utcnow()

    # 在审批历史表中插入一条记录
    approval_history = ApprovalHistory(
        approval_id=approval_id,
        status=status,
        approved_by=session['user_id'],
        approval_date=datetime.utcnow(),
        comments=comments
    )

    # 将新的审批历史记录保存到数据库
    db.session.add(approval_history)
    db.session.commit()

    # 发送通知给请求审批的用户
    send_notification(
        approval.requested_by,  # 通知给提交审批请求的用户
        f"您的审批请求已被{status}。",
        "提交的审批",
        approval_id  # 将审批 ID 作为通知的相关 ID
    )

    flash("审批处理成功", "success")
    return redirect(url_for('main.view_approvals', project_id=approval.project_id))


# 管理用户 - 仅管理员可访问
@main_bp.route('/admin/users')
def manage_users():
    if session.get('role') != '管理员':
        return "无权访问此页面", 403
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

# 管理员编辑任意用户的信息
@main_bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('role') != '管理员':
        return "无权访问此页面", 403
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            user.first_name = request.form['first_name']
            user.last_name = request.form['last_name']
            user.email = request.form['email']
            user.role = request.form['role']
            user.status = request.form['status']
            
            db.session.commit()
            flash("用户信息更新成功", "info")
            return redirect(url_for('main.manage_users'))
        
        except Exception as e:
            db.session.rollback()
            flash("更新用户信息失败，请重试。", "error")
    
    return render_template('edit_user.html', user=user)

# 激活用户 - 仅管理员可访问
@main_bp.route('/admin/users/<int:user_id>/approve')
def approve_user(user_id):
    if session.get('role') != '管理员':
        return "无权访问此页面", 403

    user = User.query.get_or_404(user_id)
    user.status = "激活"
    db.session.commit()
    flash("用户已激活", "info")
    return redirect(url_for('main.manage_users'))

# 普通用户和管理员编辑个人信息
@main_bp.route('/profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get_or_404(session['user_id'])

    if request.method == 'POST':
        try:
            user.first_name = request.form['first_name']
            user.last_name = request.form['last_name']
            
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            if old_password and new_password:
                if user.check_password(old_password):
                    user.set_password(new_password)
                else:
                    flash("旧密码错误，请重试。", "error")
                    return render_template('edit_profile.html', user=user)

            db.session.commit()

            # 发送通知给用户个人信息更新成功
            send_notification(
                user.user_id, 
                f"您的个人信息已成功更新。", 
                "个人信息更新"
            )

            flash("个人信息更新成功", "profile")
            return redirect(url_for('main.index'))

        except Exception as e:
            db.session.rollback()
            flash("更新个人信息失败，请重试。", "error")

    return render_template('edit_profile.html', user=user)


@main_bp.route('/approval/<int:approval_id>')
def approval_detail(approval_id):
    approval = Approval.query.get_or_404(approval_id)
    return render_template('approval_detail.html', approval=approval)

@main_bp.route('/projects/<int:project_id>/members', methods=['GET', 'POST'])
def project_members_detail(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    project = Project.query.get_or_404(project_id)
    project_members = ProjectMember.query.filter_by(project_id=project_id).all()
    all_users = User.query.all()  # 获取所有用户
    is_admin = session.get('role') == '管理员'

    # 确保管理员或项目成员才能查看
    if not is_admin:
        flash('您没有权限查看项目成员', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        user_id = request.form['user_id']  # 新成员的 user_id
        role = request.form['role']  # 新成员的角色

        # 添加新的项目成员
        new_member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        db.session.add(new_member)
        db.session.commit()

        flash("项目成员添加成功", "success")
        return redirect(url_for('main.project_members_detail', project_id=project_id))

    return render_template('project_members_detail.html', project=project, project_members=project_members, is_admin=is_admin, all_users=all_users)

@main_bp.route('/projects/<int:project_id>/edit_member/<int:member_id>', methods=['GET', 'POST'])
def edit_project_member(project_id, member_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    project = Project.query.get_or_404(project_id)
    member = ProjectMember.query.get_or_404(member_id)

    # 确保是管理员或项目负责人才能修改成员
    if session['role'] != '管理员' and member.user_id != session['user_id'] and member.role != '项目负责人':
        return "无权限修改成员信息", 403

    if request.method == 'POST':
        new_role = request.form['role']
        old_role = member.role
        member.role = new_role
        db.session.commit()

        # 发送通知给被修改的成员
        send_notification(
            member.user_id,
            f"您的角色已被更改为 {new_role}。",
            "项目信息变动",
            project_id
        )

        # # 如果角色变动涉及管理员或负责人，需要发送通知给其他相关成员
        # if old_role != new_role:
        #     send_notification(
        #         project_id, 
        #         f"项目成员 {member.user_id} 的角色已变更为 {new_role}。",
        #         "项目信息变动",
        #         project_id
        #     )

        flash("项目成员角色更新成功", "success")
        return redirect(url_for('main.project_members_detail', project_id=project_id))

    return render_template('edit_member.html', project=project, member=member)



@main_bp.route('/projects/<int:project_id>/remove_member/<int:member_id>', methods=['POST'])
def remove_project_member(project_id, member_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    project = Project.query.get_or_404(project_id)
    member = ProjectMember.query.get_or_404(member_id)

    # 确保是管理员或项目负责人才能删除成员
    if session['role'] != '管理员' and member.user_id != session['user_id'] and member.role != '项目负责人':
        return "无权限删除成员", 403

    db.session.delete(member)
    db.session.commit()

    flash("项目成员已被移除", "success")
    return redirect(url_for('main.project_members_detail', project_id=project_id))

@main_bp.route('/projects/<int:project_id>/add_member', methods=['POST'])
def add_project_member(project_id):
    if 'user_id' not in session or session.get('role') != '管理员':
        flash('无权限操作', 'error')
        return redirect(url_for('main.project_detail', project_id=project_id))

    user_id = request.form.get('user_id')
    role = request.form.get('role')

    # 添加新成员
    if not user_id or not role:
        flash('请填写所有字段', 'error')
        return redirect(url_for('main.project_detail', project_id=project_id))

    # 验证用户是否存在
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在', 'error')
        return redirect(url_for('main.project_detail', project_id=project_id))

    # 添加项目成员
    new_member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
    db.session.add(new_member)
    db.session.commit()

    flash('项目成员添加成功', 'success')
    return redirect(url_for('main.project_detail', project_id=project_id))

@main_bp.route('/approvals/<int:approval_id>/history')
def approval_history(approval_id):
    approval = Approval.query.get_or_404(approval_id)
    history = ApprovalHistory.query.filter_by(approval_id=approval_id).all()

    return render_template('approval_history.html', approval=approval, history=history)

@main_bp.route('/notification/<int:notification_id>')
def view_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    notification.read = True
    db.session.commit()
    return render_template('view_notification.html', notification=notification)

@main_bp.route('/notifications/<int:notification_id>')
def notification_detail(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    return render_template('notification_detail.html', notification=notification)

# 标记通知为已读
@main_bp.route('/notifications/<int:notification_id>/mark_read', methods=['POST'])
def mark_notification_as_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)

    # 确保只有当前用户才可以修改他们的通知
    if notification.user_id != session['user_id']:
        return "无权限操作", 403

    notification.read = True
    db.session.commit()

    flash("通知已标记为已读", "success")
    return redirect(url_for('main.view_notifications'))  # 跳转到通知列表


# 删除通知
@main_bp.route('/notifications/<int:notification_id>/delete', methods=['POST'])
def delete_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)

    # 确保只有当前用户才可以删除他们的通知
    if notification.user_id != session['user_id']:
        return "无权限操作", 403

    db.session.delete(notification)
    db.session.commit()

    flash("通知已删除", "success")
    return redirect(url_for('main.view_notifications'))  # 跳转到通知列表

# 显示用户的所有通知
@main_bp.route('/notifications')
def view_notifications():
    notifications = Notification.query.filter_by(user_id=session['user_id']).all()
    return render_template('notifications_list.html', notifications=notifications)

@main_bp.route('/all_messages', methods=['GET'])
def all_messages():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    # 获取当前用户接收和已发送的所有消息
    received_messages = Message.query.filter_by(receiver_id=user_id).order_by(Message.created_at.desc()).all()
    sent_messages = Message.query.filter_by(sender_id=user_id).order_by(Message.created_at.desc()).all()

    return render_template('all_messages.html', 
                           received_messages=received_messages,
                           sent_messages=sent_messages)


@main_bp.route('/delete_message/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # 获取当前用户
    user_id = session['user_id']

    # 查找该消息
    message = Message.query.filter_by(message_id=message_id).first()

    # 确保消息存在并且是该用户的消息
    if message and (message.receiver_id == user_id or message.sender_id == user_id):
        try:
            db.session.delete(message)  # 删除消息
            db.session.commit()  # 提交更改
            flash('消息删除成功', 'success')
        except Exception as e:
            db.session.rollback()  # 如果删除失败，回滚事务
            flash('删除消息时发生错误', 'danger')
    else:
        flash('消息不存在或没有权限删除', 'danger')

    # 删除后重定向回消息列表
    return redirect(url_for('main.all_messages'))


@main_bp.route('/message/<int:message_id>', methods=['GET'])
def message_detail(message_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    # 获取消息详情
    message = Message.query.get_or_404(message_id)

    # 确保该消息是当前用户的消息
    if message.receiver_id != user_id and message.sender_id != user_id:
        return redirect(url_for('main.index'))

    return render_template('message_detail.html', message=message)


@main_bp.route('/send_message', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        sender_id = session.get('user_id')  # 获取发送者的ID
        receiver_id = request.form.get('receiver_id')  # 获取表单中的收件人ID
        content = request.form['content']  # 获取消息内容

        # 确保 receiver_id 是有效的数字
        if not receiver_id:
            flash('请选择收件人', 'send_message_error')  # 使用具体类别
            return redirect(url_for('main.send_message'))
        
        try:
            receiver_id = int(receiver_id)
        except ValueError:
            flash('无效的收件人', 'send_message_error')  # 使用具体类别
            return redirect(url_for('main.send_message'))

        # 确保 receiver_id 是有效的用户 ID
        receiver = User.query.filter_by(user_id=receiver_id).first()  # 这里使用 user_id 而不是 usr_id
        if not receiver:
            flash('收件人不存在', 'send_message_error')  # 使用具体类别
            return redirect(url_for('main.send_message'))

        # 确保内容不为空
        if not content.strip():
            flash('消息内容不能为空', 'send_message_error')  # 使用具体类别
            return redirect(url_for('main.send_message'))

        # 创建并保存消息
        new_message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
        db.session.add(new_message)
        db.session.commit()

        flash('消息发送成功！', 'send_message_success')  # 使用具体类别
        return redirect(url_for('main.index'))

    # 获取所有用户用于选择收件人
    users = User.query.filter(User.user_id != session.get('user_id')).all()  # 排除当前用户
    return render_template('send_message.html', users=users)

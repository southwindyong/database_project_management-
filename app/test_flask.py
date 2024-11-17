from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config.Config')  # 加载配置

db = SQLAlchemy(app)

# 测试数据库连接的模型（可选）
class TestModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

@app.route('/test-db')
def test_db_connection():
    try:
        # 尝试创建数据库表，若成功表示连接正常
        db.create_all()  # 创建所有模型对应的表
        # 插入一条简单的数据
        test_entry = TestModel(name="Test User")
        db.session.add(test_entry)
        db.session.commit()  # 提交事务

        # 查询插入的数据，检查是否成功
        test_record = TestModel.query.first()
        if test_record:
            return jsonify(message="Database connection successful!", data={"id": test_record.id, "name": test_record.name})
        else:
            return jsonify(message="Database connected, but no data found.")
    except Exception as e:
        return jsonify(message="Database connection failed.", error=str(e))

if __name__ == "__main__":
    app.run(debug=True)

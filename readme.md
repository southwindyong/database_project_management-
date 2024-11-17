### 1. 代码获取
通过 Git 克隆项目到本地：
```bash
git clone https://github.com/southwindyong/database_project_management-.git
cd database_project_management-
```
### 2. 安装依赖
安装项目所需的依赖：

```bash
pip install -r requirements.txt
```
### 3. 配置数据库
- 安装 PostgreSQL 数据库。
- 创建数据库：
   ```sql
   CREATE DATABASE management_system;
   ```
- 配置 .env 文件：
   在 app 目录下创建 .env 文件，填入以下内容（根据实际的数据库信息修改）：
   ```php
   DATABASE_URL=postgresql://<用户名>:<密码>@localhost/management_system
   SECRET_KEY=<随机生成的密钥>
   ```
### 4. 初始化数据库
- 初始化迁移环境：
   ```bash
   Copy code
   flask db init
   ```
   这将生成一个 migrations 文件夹，用于管理数据库迁移。

- 生成迁移脚本：
   ```bash
   Copy code
   flask db migrate -m "Initial migration"
   ```
- 应用迁移脚本到数据库：
```bash
Copy code
flask db upgrade
```
### 5. 运行系统
启动 Flask 开发服务器：
```bash
flask run
```
系统将在本地运行，并可以通过浏览器访问。
"""ORM 模型聚合模块。

Alembic 执行自动迁移时会加载本模块，
确保所有业务模型已经注册到 Base.metadata。
"""

# 后续新增模型时，需要在这里统一导入。
#
# 示例：
# from app.models.user import User
# from app.models.role import Role
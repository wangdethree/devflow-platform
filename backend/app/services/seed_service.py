"""系统角色、权限与可选管理员的幂等初始化服务。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import ALL_PERMISSIONS, PROJECT_CREATE
from app.core.security import hash_password
from app.models.permission import Permission
from app.models.project_role import ProjectRole
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole


ROLE_PERMISSIONS = {
    "Admin": set(ALL_PERMISSIONS),
    "User": {PROJECT_CREATE},
}


async def seed_reference_data(session: AsyncSession) -> None:
    """幂等初始化系统角色、权限及角色权限关联。"""

    roles: dict[str, Role] = {}
    for name, description in {
        "Admin": "系统管理员",
        "User": "普通系统用户",
    }.items():
        role = (
            await session.execute(select(Role).where(Role.name == name))
        ).scalar_one_or_none()
        if role is None:
            role = Role(name=name, description=description)
            session.add(role)
            await session.flush()
        roles[name] = role

    permissions: dict[str, Permission] = {}
    for code, description in ALL_PERMISSIONS.items():
        permission = (
            await session.execute(
                select(Permission).where(Permission.code == code)
            )
        ).scalar_one_or_none()
        if permission is None:
            permission = Permission(code=code, description=description)
            session.add(permission)
            await session.flush()
        permissions[code] = permission

    existing_relations = set(
        (
            await session.execute(
                select(
                    RolePermission.role_id,
                    RolePermission.permission_id,
                )
            )
        ).all()
    )
    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        for code in permission_codes:
            relation = (roles[role_name].id, permissions[code].id)
            if relation not in existing_relations:
                session.add(
                    RolePermission(
                        role_id=relation[0],
                        permission_id=relation[1],
                    )
                )

    for name, description in {
        "Owner": "项目负责人",
        "Developer": "项目开发人员",
        "Viewer": "项目只读成员",
    }.items():
        project_role = (
            await session.execute(
                select(ProjectRole).where(ProjectRole.name == name)
            )
        ).scalar_one_or_none()
        if project_role is None:
            session.add(ProjectRole(name=name, description=description))
    await session.commit()


async def seed_admin(
    session: AsyncSession,
    *,
    email: str,
    username: str,
    password: str,
) -> User:
    """幂等创建管理员，密码仅来自命令行参数。"""

    user = (
        await session.execute(
            select(User).where(User.email == email.lower())
        )
    ).scalar_one_or_none()
    if user is None:
        user = User(
            username=username,
            email=email.lower(),
            password_hash=hash_password(password),
        )
        session.add(user)
        await session.flush()

    admin_role = (
        await session.execute(select(Role).where(Role.name == "Admin"))
    ).scalar_one()
    relation = (
        await session.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == admin_role.id,
            )
        )
    ).scalar_one_or_none()
    if relation is None:
        session.add(UserRole(user_id=user.id, role_id=admin_role.id))
    await session.commit()
    await session.refresh(user)
    return user

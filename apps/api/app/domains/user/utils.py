import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import emails  # type: ignore
import jwt
from jinja2 import Template
from jwt.exceptions import InvalidTokenError

from app.core import security
from app.core.config import get_settings

settings = get_settings()
# 配置日志记录器
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================== 邮件数据模型 ========================

@dataclass
class EmailData:
    """邮件数据容器类（数据类）。
    
    属性：
    - html_content：邮件 HTML 内容
    - subject：邮件主题
    """
    html_content: str
    subject: str


# ======================== 邮件模板渲染 ========================

def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    """
    渲染邮件 Jinja2 模板。
    
    参数：
    - template_name：模板文件名（如 "test_email.html"）
    - context：模板上下文变量字典（如 {"project_name": "...", "email": "..."}）
    
    返回值：
    - 渲染后的 HTML 字符串
    
    流程：
    1. 从 app/email-templates/build/ 目录读取模板文件
    2. 使用 Jinja2 Template 引擎渲染，传入 context 变量
    3. 返回最终 HTML （通常用于邮件内容）
    """
    template_str = (
        Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    """
    通过 SMTP 发送邮件。
    
    参数：
    - email_to：收件人邮箱
    - subject：邮件主题
    - html_content：邮件 HTML 内容
    
    前置条件：
    - settings.emails_enabled 必须为 True（即 SMTP_HOST 和 EMAILS_FROM_EMAIL 已配置）
    - 否则抛出 AssertionError
    
    SMTP 配置：
    - 根据 SMTP_TLS / SMTP_SSL 标志选择加密方式
    - 若配置了 SMTP_USER/PASSWORD，则加入认证信息
    
    日志：
    - 发送结果记录到 logger.info
    """
    assert settings.emails_enabled, "no provided configuration for email variables"
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, smtp=smtp_options)
    logger.info(f"send email result: {response}")


# ======================== 邮件内容生成器 ========================

def generate_test_email(email_to: str) -> EmailData:
    """
    生成测试邮件。
    
    用途：邮件配置验证或测试，通常不在生产流程中使用。
    
    参数：
    - email_to：收件人邮箱
    
    返回值：
    - EmailData 对象，包含测试邮件的主题和 HTML 内容
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    """
    生成密码重置邮件。
    
    参数：
    - email_to：收件人邮箱
    - email：用户邮箱（用于邮件正文展示）
    - token：密码重置令牌（由 generate_password_reset_token 生成）
    
    返回值：
    - EmailData 对象，包含重置邮件的主题和 HTML 内容
    
    邮件内容：
    - 包含重置链接：{FRONTEND_HOST}/reset-password?token={token}
    - 链接有效期：EMAIL_RESET_TOKEN_EXPIRE_HOURS（默认 48 小时）
    - 用户点击链接后在前端输入新密码
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    """
    生成新账户邮件（用户注册成功邮件）。
    
    参数：
    - email_to：收件人邮箱
    - username：用户名（通常是邮箱）
    - password：临时密码或初始密码
    
    返回值：
    - EmailData 对象，包含新账户邮件的主题和 HTML 内容
    
    注意：
    - 邮件中包含临时密码，建议提醒用户首次登录后修改
    - 该功能通常用于管理员创建用户时自动发送邮件
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


# ======================== 密码重置令牌管理 ========================

def generate_password_reset_token(email: str) -> str:
    """
    生成密码重置 JWT 令牌。
    
    参数：
    - email：用户邮箱
    
    返回值：
    - JWT 令牌字符串
    
    令牌包含：
    - exp：过期时间戳（当前时间 + EMAIL_RESET_TOKEN_EXPIRE_HOURS）
    - nbf：生效时间戳（当前时间）
    - sub：令牌主体（用户邮箱）
    
    流程：
    1. 计算过期时间（有效期：48 小时）
    2. 使用 JWT HS256 算法签名
    3. 返回令牌供邮件链接使用
    
    安全性：
    - 令牌有时间限制（nbf + exp）
    - 使用服务端 SECRET_KEY 签名，防伪造
    """
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    """
    验证密码重置令牌。
    
    参数：
    - token：密码重置 JWT 令牌
    
    返回值：
    - 邮箱字符串（令牌有效）
    - None（令牌无效、过期或签名错误）
    
    流程：
    1. 使用 settings.SECRET_KEY 解码 JWT
    2. 若解码成功，返回 sub（邮箱）
    3. 若捕获 InvalidTokenError（过期、签名错误等），返回 None
    
    用途：
    - 验证邮件中点击的重置链接中的令牌
    - 若返回邮箱，说明用户可以重置密码
    - 若返回 None，说明令牌已过期或被篡改
    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None

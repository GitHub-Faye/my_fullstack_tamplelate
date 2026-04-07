from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_user_signup_task(self, user_id: str, email: str, full_name: str | None = None) -> bool:
    """
    异步处理用户注册后续任务
    
    参数:
        user_id: 用户ID (UUID字符串)
        email: 用户邮箱
        full_name: 用户姓名 (可选)
    
    返回:
        bool: 处理是否成功
    """
    try:
        logger.info(
            "processing_user_signup",
            user_id=user_id,
            email=email,
            full_name=full_name,
            task_id=self.request.id,
        )
        
        # TODO: 实现注册后续处理
        # 例如：发送欢迎邮件、创建默认数据、通知管理员等
        
        # 示例：发送欢迎邮件（可以调用 email_tasks）
        # from app.tasks.email_tasks import send_email_task
        # send_email_task.delay(
        #     email_to=email,
        #     subject="欢迎注册",
        #     html_content=f"<h1>欢迎 {full_name or email}!</h1>"
        # )
        
        logger.info(
            "user_signup_processed",
            user_id=user_id,
            email=email,
        )
        return True
        
    except Exception as exc:
        logger.error(
            "user_signup_processing_failed",
            user_id=user_id,
            email=email,
            error=str(exc),
            retry_count=self.request.retries,
        )
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=5)
def cleanup_inactive_users_task(self) -> int:
    """
    定期清理不活跃用户
    
    返回:
        int: 清理的用户数量
    """
    try:
        logger.info(
            "cleaning_inactive_users",
            task_id=self.request.id,
        )
        
        # TODO: 实现清理逻辑
        # 例如：删除超过30天未激活的账户
        cleaned_count = 0
        
        logger.info(
            "inactive_users_cleaned",
            cleaned_count=cleaned_count,
        )
        return cleaned_count
        
    except Exception as exc:
        logger.error(
            "cleanup_inactive_users_failed",
            error=str(exc),
            retry_count=self.request.retries,
        )
        raise self.retry(exc=exc, countdown=600)

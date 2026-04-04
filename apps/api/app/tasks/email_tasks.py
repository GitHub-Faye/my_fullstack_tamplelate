from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def send_email_task(self, email_to: str, subject: str, html_content: str) -> bool:
    """
    异步发送邮件任务
    
    参数:
        email_to: 收件人邮箱
        subject: 邮件主题
        html_content: HTML 内容
    
    返回:
        bool: 发送是否成功
    """
    try:
        # TODO: 实现邮件发送逻辑
        # from app.domains.user.utils import send_email
        # send_email(email_to=email_to, subject=subject, html_content=html_content)
        print(f"Sending email to {email_to}: {subject}")
        return True
    except Exception as exc:
        # 重试机制：5分钟后重试
        raise self.retry(exc=exc, countdown=300)

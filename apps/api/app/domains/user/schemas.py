from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """用户基础信息"""
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """创建用户请求"""
    password: str


class UserUpdate(BaseModel):
    """更新用户请求"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class User(UserBase):
    """用户响应模型"""
    id: int
    disabled: bool = False
    
    class Config:
        from_attributes = True


class UserInDB(User):
    """数据库中的用户（包含密码）"""
    hashed_password: str


class Token(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token 数据"""
    username: Optional[str] = None

from fastapi import APIRouter, Depends, HTTPException
from config.db_config import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import User
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UserUpdateRequest, UserChangePasswordRequest
from crud import users
from utils.response import success_response
from utils.auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["users"])

@router.post("/register")
async def register_user(user_data:UserRequest,db: AsyncSession = Depends(get_db)):
    exiting_user = await users.get_user(db, user_data.username)
    if exiting_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    new_user = await users.create_user(db, user_data)
    token = await users.create_token(db, new_user.id)
    response_data = UserAuthResponse(token=token, userInfo=UserInfoResponse.model_validate(new_user))
    return success_response(message="注册成功", data=response_data)

@router.post("/login")
async def login(user_data:UserRequest,db: AsyncSession = Depends(get_db)):
    user = await users.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    token = await users.create_token(db, user.id)
    response_data = UserAuthResponse(token=token, userInfo=UserInfoResponse.model_validate(user))
    return success_response(message="登录成功", data=response_data)

@router.get("/info")
async def get_user_info(user: User = Depends(get_current_user)):
    return success_response(message="获取用户信息成功", data=UserInfoResponse.model_validate(user))

@router.put("/update")
async def update_user_info(user_data: UserUpdateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await users.update_user_info(db, user.username, user_data)
    return success_response(message="更新用户信息成功", data=UserInfoResponse.model_validate(user))

@router.put("/password")
async def update_password(password_data: UserChangePasswordRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await users.change_user_password(db, user, password_data.old_password, password_data.new_password)
    if not res:
        raise HTTPException(status_code=400, detail="旧密码错误")
    return success_response(message="修改密码成功")


@router.delete("/account", summary="注销当前账户")
async def delete_my_account(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    success = await users.delete_user_account(db, current_user.id)
    if not success:
        raise HTTPException(status_code=500, detail="注销失败，服务器内部错误或用户不存在")
    return success_response(message="账户及其所有数据已永久注销")
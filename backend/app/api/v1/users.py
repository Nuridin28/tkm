"""
User management API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from app.core.auth import require_role, get_current_user
from app.core.database import get_supabase_admin
from app.models.schemas import UserCreate, UserResponse
from typing import Dict, Any, List

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> List[UserResponse]:
    """List all users (admin only)"""
    supabase_admin = get_supabase_admin()
    try:
        # Загружаем пользователей
        result = supabase_admin.table("users").select("*").order("created_at", desc=True).execute()
        
        # Загружаем все департаменты для маппинга
        dept_result = supabase_admin.table("departments").select("id, name").execute()
        dept_map = {dept["id"]: dept["name"] for dept in (dept_result.data if dept_result.data else [])}
        
        users = []
        for u in (result.data if result.data else []):
            user_dict = dict(u)
            # Добавляем название департамента если есть
            if user_dict.get("department_id") and user_dict["department_id"] in dept_map:
                user_dict["department_name"] = dept_map[user_dict["department_id"]]
            users.append(UserResponse(**user_dict))
        
        return users
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to list users: {str(e)}")


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
):
    """Create a new user (admin only)"""
    supabase_admin = get_supabase_admin()
    
    try:
        # Создать пользователя через Supabase Admin API
        auth_response = supabase_admin.auth.admin.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "email_confirm": True,
            "user_metadata": {
                "name": user_data.name,
                "role": user_data.role.value
            }
        })
        
        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        # Создать профиль в public.users
        profile_response = supabase_admin.table("users").insert({
            "id": auth_response.user.id,
            "email": user_data.email,
            "name": user_data.name,
            "role": user_data.role.value,
            "department_id": user_data.department_id
        }).execute()
        
        if not profile_response.data:
            # Пользователь создан, но профиль не создан - можно исправить вручную
            print(f"Warning: User {auth_response.user.id} created but profile not created")
        
        return UserResponse(
            id=auth_response.user.id,
            email=user_data.email,
            name=user_data.name,
            role=user_data.role.value,
            department_id=user_data.department_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create user: {str(e)}")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
):
    """Delete a user (admin only)"""
    supabase_admin = get_supabase_admin()
    
    try:
        # Проверить, не пытается ли пользователь удалить самого себя
        if user_id == current_user.get("id"):
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Проверить, есть ли тикеты, назначенные на этого пользователя
        tickets_result = supabase_admin.table("tickets").select("id").eq("assigned_to", user_id).limit(1).execute()
        if tickets_result.data:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete user with assigned tickets. Please reassign tickets first."
            )
        
        # Удалить профиль из public.users
        supabase_admin.table("users").delete().eq("id", user_id).execute()
        
        # Удалить пользователя из auth.users через Admin API
        supabase_admin.auth.admin.delete_user(user_id)
        
        return {"success": True, "message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete user: {str(e)}")


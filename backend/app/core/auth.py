from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from app.core.database import get_supabase
from typing import Optional

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase)
) -> dict:
    try:
        token = credentials.credentials
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        user_dict = user.user.model_dump() if hasattr(user.user, 'model_dump') else user.user
        return user_dict
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )


async def get_user_role_from_db(user_id: str, supabase: Client) -> Optional[str]:
    try:
        from app.core.database import get_supabase_admin
        try:
            admin_client = get_supabase_admin()
            result = admin_client.table("users").select("role").eq("id", user_id).single().execute()
            if result.data:
                role = result.data.get("role")
                print(f"✅ Role loaded from DB: {role} for user {user_id}")
                return role
        except Exception as admin_error:
            print(f"Admin client not available, trying regular client: {admin_error}")

        result = supabase.table("users").select("role").eq("id", user_id).single().execute()
        if result.data:
            role = result.data.get("role")
            print(f"✅ Role loaded from DB (regular): {role} for user {user_id}")
            return role
    except Exception as e:
        print(f"❌ Error loading user role from DB: {e}")
        import traceback
        traceback.print_exc()
    return None


def require_role(allowed_roles: list[str]):
    async def role_checker(
        user: dict = Depends(get_current_user),
        supabase: Client = Depends(get_supabase)
    ) -> dict:
        user_id = user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )

        user_role = await get_user_role_from_db(user_id, supabase)

        if not user_role:
            user_role = user.get("role") or user.get("user_metadata", {}).get("role")

        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User role not found"
            )

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {allowed_roles}, but user has: {user_role}"
            )

        return user
    return role_checker


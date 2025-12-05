"""
Departments API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from app.core.auth import require_role
from app.core.database import get_supabase_admin
from app.models.schemas import DepartmentCreate, DepartmentResponse
from typing import Dict, Any, List, Optional

router = APIRouter()


@router.get("", response_model=List[DepartmentResponse])
async def list_departments(
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> List[DepartmentResponse]:
    """List all departments"""
    try:
        supabase = get_supabase_admin()
        print(f"Loading departments for user: {user.get('id')}")
        
        # Попробуем без order сначала
        result = supabase.table("departments").select("*").execute()
        print(f"Departments query result: {len(result.data) if result.data else 0} departments")
        
        departments = []
        for d in (result.data if result.data else []):
            try:
                # Преобразовать datetime в строки для JSON
                dept_dict = dict(d)
                if 'created_at' in dept_dict and dept_dict['created_at']:
                    dept_dict['created_at'] = str(dept_dict['created_at'])
                if 'updated_at' in dept_dict and dept_dict['updated_at']:
                    dept_dict['updated_at'] = str(dept_dict['updated_at'])
                # Убедимся, что description есть (может отсутствовать в старых данных)
                if 'description' not in dept_dict:
                    dept_dict['description'] = None
                departments.append(DepartmentResponse(**dept_dict))
            except Exception as parse_error:
                print(f"Error parsing department {d.get('id')}: {parse_error}")
                continue
        
        print(f"Returning {len(departments)} departments")
        return departments
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error loading departments: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load departments: {str(e)}")


@router.post("", response_model=DepartmentResponse)
async def create_department(
    department_data: DepartmentCreate,
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> DepartmentResponse:
    """Create a new department (admin only)"""
    supabase = get_supabase_admin()
    try:
        insert_data = {
            "name": department_data.name
        }
        # Добавляем description только если он указан и колонка существует
        if department_data.description:
            insert_data["description"] = department_data.description
        
        result = supabase.table("departments").insert(insert_data).execute()
        
        if result.data:
            dept_dict = dict(result.data[0])
            # Преобразовать datetime в строки
            if 'created_at' in dept_dict and dept_dict['created_at']:
                dept_dict['created_at'] = str(dept_dict['created_at'])
            if 'updated_at' in dept_dict and dept_dict['updated_at']:
                dept_dict['updated_at'] = str(dept_dict['updated_at'])
            return DepartmentResponse(**dept_dict)
        raise HTTPException(status_code=400, detail="Failed to create department")
    except Exception as e:
        print(f"Error creating department: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to create department: {str(e)}")


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: str,
    department_data: DepartmentCreate,
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> DepartmentResponse:
    """Update department (admin only)"""
    supabase = get_supabase_admin()
    try:
        update_data = {
            "name": department_data.name
        }
        # Добавляем description только если он указан
        if department_data.description is not None:
            update_data["description"] = department_data.description
        
        result = supabase.table("departments").update(update_data).eq("id", department_id).execute()
        
        if result.data:
            dept_dict = dict(result.data[0])
            # Преобразовать datetime в строки
            if 'created_at' in dept_dict and dept_dict['created_at']:
                dept_dict['created_at'] = str(dept_dict['created_at'])
            if 'updated_at' in dept_dict and dept_dict['updated_at']:
                dept_dict['updated_at'] = str(dept_dict['updated_at'])
            return DepartmentResponse(**dept_dict)
        raise HTTPException(status_code=404, detail="Department not found")
    except Exception as e:
        print(f"Error updating department: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to update department: {str(e)}")


@router.delete("/{department_id}")
async def delete_department(
    department_id: str,
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> Dict[str, Any]:
    """Delete department (admin only)"""
    supabase = get_supabase_admin()
    try:
        # Проверить, есть ли тикеты или пользователи в этом департаменте
        tickets_result = supabase.table("tickets").select("id").eq("department_id", department_id).limit(1).execute()
        users_result = supabase.table("users").select("id").eq("department_id", department_id).limit(1).execute()
        
        if tickets_result.data or users_result.data:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete department with associated tickets or users"
            )
        
        supabase.table("departments").delete().eq("id", department_id).execute()
        return {"success": True, "message": "Department deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete department: {str(e)}")


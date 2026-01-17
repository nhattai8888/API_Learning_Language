from pydantic import BaseModel
from typing import Optional, List

class RoleCreate(BaseModel):
    code: str
    name: str

class RoleOut(BaseModel):
    id: str
    code: str
    name: str
    status: str

class PermissionCreate(BaseModel):
    code: str
    module: str
    description: Optional[str] = None

class PermissionOut(BaseModel):
    id: str
    code: str
    module: str
    description: Optional[str] = None
    status: str

class AssignRoleRequest(BaseModel):
    user_id: str
    role_codes: List[str]

class AssignPermissionToRoleRequest(BaseModel):
    role_code: str
    permission_codes: List[str]

from stark.service import v1

from . import models

class RoleConfig(v1.StarkConfig):
    list_display = ['id','title']
v1.site.register(models.Role,RoleConfig)

class DepartmentConfig(v1.StarkConfig):
    list_display = ['id','caption']
v1.site.register(models.Department,DepartmentConfig)

class UserInfoConfig(v1.StarkConfig):
    def display_gender(self,obj=None,is_header=False):
        if is_header:
            return '性别'
        return obj.get_gender_display()   # 拿到字段

    def display_depart(self,obj=None,is_header=False):
        if is_header:
            return '部门'
        return obj.depart.caption

    def display_roles(self,obj=None,is_header=False):
        if is_header:
            return '角色'
        return obj.roles.title

    list_display = ['id','name','email',display_depart,display_gender,display_roles]

    comb_filter = ['gender','depart','roles']
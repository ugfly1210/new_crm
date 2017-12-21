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
        html = []
        role_list = obj.roles.all()
        for role in role_list:
            html.append(role.title)
        return ','.join(html)

    list_display = ['id','name','email',display_depart,display_gender,display_roles]

    # 组合搜索
    comb_filter = [  # 将配置项,改成对象的形式.  这个类里面是有两个参数的
        v1.FilterOption('gender',is_choice=True),
        v1.FilterOption('depart'),
        v1.FilterOption('roles',True),
        # 这是三个option对象
    ]

v1.site.register(models.UserInfo,UserInfoConfig)

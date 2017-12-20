from django.shortcuts import HttpResponse
from django.conf.urls import url,include
from django.utils.safestring import mark_safe
from stark.service import v1
from app01 import models
from django.forms import ModelForm


class UserInfoModelForm(ModelForm):
    class Meta:
        model = models.UserInfo
        fields = ["name","password"]
        error_messages = {
            "name":{
                'required':'用户名不能为空'
            }
        }



class UserInfoConfig(v1.StarkConfig):

    list_display = ['id', 'name','age','sex']

    show_add_btn = True
    show_search_form = True
    model_form_class = UserInfoModelForm
    search_fields = ['name__contains','sex']

    '''actions批量操作相关'''
    show_actions = True
    def multi_del(self,request): # 找函数的时候,传了一个request参数
        print(request.POST.getlist('pk'))
        pk_list = request.POST.getlist('pk')
        self.model_class.objects.filter(id__in=pk_list).delete()
    multi_del.short_desc = '批量删除'

    def multi_init(self,request): # 找函数的时候,传了一个request参数
        # print(request.POST.getlist('pk'))
        # pk_list = request.POST.getlist('pk')
        # self.model_class.objects.filter(id__in=pk_list).delete()
        return HttpResponse('Do you love me❄️❄️❄️?')
    multi_init.short_desc = '批量初始化'



    actions = [multi_del,multi_init] # 只传函数名


    def extra_url(self):

        url_list = [
            url(r'^$', self.func)
        ]
        return url_list

    def func(self,request):
        return HttpResponse("...")





v1.site.register(models.UserInfo,UserInfoConfig) # UserInfoConfig(UserInfo,)


class RoleConfig(v1.StarkConfig):
    list_display = ['name',]
v1.site.register(models.Role,RoleConfig) # StarkConfig(Role)


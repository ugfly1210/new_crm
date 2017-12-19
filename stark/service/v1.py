from django.conf.urls import url,include
from django.shortcuts import HttpResponse,render,reverse,redirect
from django.utils.safestring import mark_safe
from django.forms import ModelForm
from stark.utils.page import Pagination




class StarkConfig(object):

    def __init__(self,model_class,site):
        self.model_class = model_class
        self.site = site

    # 用户访问url
    def get_urls(self):
        app_model_name = (self.model_class._meta.app_label, self.model_class._meta.model_name,)
        url_patterns = [
            url(r'^$', self.changelist_view, name="%s_%s_list" % app_model_name),
            url(r'^add/$', self.add_view, name="%s_%s_add" % app_model_name),
            url(r'^(\d+)/delete/$', self.delete_view, name="%s_%s_delete" % app_model_name),
            url(r'^(\d+)/change/$', self.change_view, name="%s_%s_change" % app_model_name),
        ]

        url_patterns.extend(self.extra_url())

        return url_patterns

    def extra_url(self):
        return []

    @property
    def urls(self):
        return self.get_urls()

    # 显示哪几列
    list_display = []
    def get_list_display(self):
        data = []
        if self.list_display:
            data.extend(self.list_display)
            data.append(StarkConfig.edit)
            data.append(StarkConfig.delete)
            data.insert(0,StarkConfig.checkbox)
        return data

    # 是否显示增加按钮
    show_add_btn = True
    def get_show_btn(self):
        return self.show_add_btn

    # model_form_class
    model_form_class = None
    def get_model_form_class(self):
        if self.model_form_class:
            return self.model_form_class
        else:
            #方式一:
            # class AddTable(ModelForm):
            #     class Meta:
            #         model = self.model_class
            #         fields = "__all__"
            # return AddTable
            #方式二:
            meta = type("Meta",(object,),{"model":self.model_class,"fields":"__all__"})
            AddTable = type("AddTable",(ModelForm,),{"Meta":meta})
            return AddTable


    # ############# 处理请求的方法 ################

    def changelist_view(self, request, *args, **kwargs):


        #分页
        current_page = request.GET.get('page',1)
        total_count = self.model_class.objects.all().count()
        base_url = request.path_info

        page_list =Pagination(current_page,total_count,base_url,request.GET,per_page_count=2,pager_count=5)
        html = page_list.page_html()



        # 处理表头

        head_list = []
        for field_name in self.get_list_display():
            if isinstance(field_name, str):
                # 根据类和字段名称，获取字段对象的verbose_name
                verbose_name = self.model_class._meta.get_field(field_name).verbose_name
            else:
                verbose_name = field_name(self, is_header=True)
            head_list.append(verbose_name)

        # 处理表中的数据
        # [ UserInfoObj,UserInfoObj,UserInfoObj,UserInfoObj,]
        # [ UserInfo(id=1,name='alex',age=18),UserInfo(id=2,name='alex2',age=181),]
        data_list = self.model_class.objects.all()[page_list.start:page_list.end]
        new_data_list = []
        for row in data_list:
            # row是 UserInfo(id=2,name='alex2',age=181)
            # row.id,row.name,row.age
            temp = []
            for field_name in self.get_list_display():
                if isinstance(field_name, str):
                    val = getattr(row, field_name)  # # 2 alex2
                else:
                    val = field_name(self, row)
                temp.append(val)
            new_data_list.append(temp)

        return render(request, 'stark/changelist.html', {'data_list': new_data_list, 'head_list': head_list,"add_url":self.get_add_url(),"show_add_btn":self.get_show_btn(),"page_html":html})

    def add_view(self, request, *args, **kwargs):

        model_form_class = self.get_model_form_class()
        if request.method == "GET":
            form = model_form_class()
            return render(request,"stark/add_view.html",{"form":form})
        else:
            form = model_form_class(request.POST)
            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())
            else:
                return render(request, "stark/add_view.html", {"form": form})

    def delete_view(self, request, nid, *args, **kwargs):
        self.model_class.objects.filter(pk=nid).delete()
        return redirect(self.get_list_url())

    def change_view(self, request, nid, *args, **kwargs):

        obj = self.model_class.objects.filter(pk=nid).first()
        if not obj:
            return redirect(self.get_list_url())
        model_form_class = self.get_model_form_class()
        if request.method == "GET":
            form = model_form_class(instance=obj)
            return render(request,"stark/change_view.html",{"form":form})
        else:
            form = model_form_class(instance=obj,data=request.POST)
            if form.is_valid:
                form.save()
                return redirect(self.get_list_url())
            return render(request,"stark/change_view.html",{"form":form})





    def checkbox(self,obj=None,is_header=False):
        if is_header:
            return '选择'
        return mark_safe('<input type="checkbox" name="pk" value="%s" />' %(obj.id,))
    def edit(self,obj=None,is_header=False):
        if is_header:
            return '编辑'
        return mark_safe('<a href="%s">编辑</a>' %(self.get_change_url(obj.id)))
    def delete(self,obj=None,is_header=False):
        if is_header:
            return '删除'
        return mark_safe('<a href="%s">删除</a>' %(self.get_delete_url(obj.id)))


    def get_list_url(self):
        name = "shark:%s_%s_list" %(self.model_class._meta.app_label,self.model_class._meta.model_name)

        list_url = reverse(name)

        return list_url


    def get_change_url(self,nid):
        name = "shark:%s_%s_change" %(self.model_class._meta.app_label,self.model_class._meta.model_name)

        edit_url = reverse(name,args=(nid,))
        return edit_url

    def get_delete_url(self,nid):
        name = "shark:%s_%s_delete" %(self.model_class._meta.app_label,self.model_class._meta.model_name)

        delete_url = reverse(name,args=(nid,))
        return delete_url

    def get_add_url(self):
        name = "shark:%s_%s_add" %(self.model_class._meta.app_label,self.model_class._meta.model_name)

        add_url = reverse(name)
        return add_url


class StarkSite(object):

    def __init__(self):
        self._registey = {}

    def register(self,model_class,stark_config_class=None):
        if not stark_config_class:
            stark_config_class = StarkConfig

        self._registey[model_class] = stark_config_class(model_class,self)

    def get_urls(self):

        url_pattern = []

        for model_class,stark_config_obj in self._registey.items():
            # 为每一个类，创建4个URL
            """
            {
                models.UserInfo: StarkConfig(models.UserInfo,self),
                models.Role: StarkConfig(models.Role,self)
            }
            /stark/app01/userinfo/
            /stark/app01/userinfo/add/
            /stark/app01/userinfo/(\d+)/change/
            /stark/app01/userinfo/(\d+)/delete/
            """
            app_name = model_class._meta.app_label
            model_name = model_class._meta.model_name

            curd_url = url(r'^%s/%s/' %(app_name,model_name,) , (stark_config_obj.urls,None,None))
            url_pattern.append(curd_url)


        return url_pattern

    @property
    def urls(self):
        return self.get_urls(),None,"shark"


site = StarkSite()
from django.conf.urls import url,include
from django.shortcuts import HttpResponse,render,reverse,redirect
from django.utils.safestring import mark_safe
from django.forms import ModelForm
from stark.utils.page import Pagination
from django.http import QueryDict
from django.db.models import Q

class ChangeList(object):
    def __init__(self,config,queryset):

        self.config = config #这个config对应的是你starkconfig的对象,而这里init的self是changelist的对象

        self.list_display = config.get_list_display()
        self.model_class = config.model_class
        self.request = config.request  # 因为在分页里面要用到request,而这个request在config对象中有
        self.show_add_btn = config.get_show_add_btn()

        # 搜索用
        self.show_search_form = config.get_show_search_form()
        self.search_form_val = config.request.GET.get(config.search_key, '')


        # 分页
        current_page = self.request.GET.get('page', 1)
        total_count = queryset.count()
        base_url = self.request.path_info

        page_obj = Pagination(current_page, total_count, base_url, self.request.GET, per_page_count=5, max_pager_count=5)
        self.page_obj = page_obj

        self.data_list = queryset[page_obj.start:page_obj.end]


    def head_list(self):
        # 处理表头
        result = []
        for field_name in self.list_display:
            if isinstance(field_name, str):
                # 根据类和字段名称，获取字段对象的verbose_name
                verbose_name = self.model_class._meta.get_field(field_name).verbose_name
            else:
                verbose_name = field_name(self.config, is_header=True)
            result.append(verbose_name)
        return result

    def add_url(self):
        return self.config.get_add_url()


    def body_list(self):
        # 处理表中的数据
        # [ UserInfoObj,UserInfoObj,UserInfoObj,UserInfoObj,]
        # [ UserInfo(id=1,name='alex',age=18),UserInfo(id=2,name='alex2',age=181),]
        data_list = self.data_list
        new_data_list = []
        for row in data_list:
            # row是 UserInfo(id=2,name='alex2',age=181)
            # row.id,row.name,row.age
            temp = []
            for field_name in self.list_display:
                if isinstance(field_name, str):
                    val = getattr(row, field_name)  # # 2 alex2
                else:
                    val = field_name(self.config, row)
                temp.append(val)
            new_data_list.append(temp)
        # print('new_data_list===',new_data_list)
        return new_data_list

class StarkConfig(object):

    def __init__(self,model_class,site):
        self.model_class = model_class
        self.site = site

        self.request = None
        self._query_param_key = '_list_filter'
        self.search_key = '_q'  # 设置默认值


    '''给get_urls()里面统一加上一个装饰器,因为要实现页面操作完成后调回当前页面,要用到request'''
    def warp(self,view_func):
        def inner(request,*args,**kwargs):
            self.request = request
            return view_func(request,*args,**kwargs)
        return inner
# changelist_view = warp(changelist_view)


    # 用户访问url
    def get_urls(self):
        app_model_name = (self.model_class._meta.app_label, self.model_class._meta.model_name,)
        url_patterns = [
            url(r'^$', self.warp(self.changelist_view), name="%s_%s_list" % app_model_name),
            url(r'^add/$', self.warp(self.add_view), name="%s_%s_add" % app_model_name),
            url(r'^(\d+)/delete/$', self.warp(self.delete_view), name="%s_%s_delete" % app_model_name),
            url(r'^(\d+)/change/$', self.warp(self.change_view), name="%s_%s_change" % app_model_name),
        ]

        url_patterns.extend(self.extra_url())

        return url_patterns


    def extra_url(self):
        return []
    @property
    def urls(self):
        return self.get_urls()
    def get_list_url(self):
        name = "stark:%s_%s_list" % (self.model_class._meta.app_label, self.model_class._meta.model_name)
        list_url = reverse(name)
        return list_url
    def get_change_url(self, nid):
        name = "stark:%s_%s_change" % (self.model_class._meta.app_label, self.model_class._meta.model_name)

        edit_url = reverse(name, args=(nid,))
        return edit_url
    def get_delete_url(self, nid):
        name = "stark:%s_%s_delete" % (self.model_class._meta.app_label, self.model_class._meta.model_name)

        delete_url = reverse(name, args=(nid,))
        return delete_url
    def get_add_url(self):
        name = "stark:%s_%s_add" % (self.model_class._meta.app_label, self.model_class._meta.model_name)

        add_url = reverse(name)
        return add_url


    list_display = []
    def get_list_display(self):
        data = []
        if self.list_display:
            data.extend(self.list_display)
            data.append(StarkConfig.edit)
            data.append(StarkConfig.delete)
            data.insert(0,StarkConfig.checkbox)
        return data

    # 1. 定制列表显示的列
    def checkbox(self, obj=None, is_header=False):
        if is_header:
            return '选择'
        return mark_safe('<input type="checkbox" name="pk" value="%s" />' % (obj.id,))

    def edit(self, obj=None, is_header=False):
        if is_header:
            return '编辑'
        '''获取条件'''
        query_str = self.request.GET.urlencode()
        if query_str:
            '''重构'''
            params = QueryDict(mutable=True)
            params[self._query_param_key] = query_str  # 把获取到的query_str当做值给它
            return mark_safe('<a href="%s?%s">编辑</a>' % (self.get_change_url(obj.id), params.urlencode()))
            # 这里写完就应该到post请求了
        return mark_safe('<a href="%s">编辑</a>' % (self.get_change_url(obj.id)))

    def delete(self, obj=None, is_header=False):
        if is_header:
            return '删除'
        return mark_safe('<a href="%s">删除</a>' % (self.get_delete_url(obj.id)))

    # 2. 是否显示增加按钮
    show_add_btn = True
    def get_show_add_btn(self):
        return self.show_add_btn

    # 3. model_form_class
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

            # class AddTable(ModelForm):
            #     class Meta:
            #         model = self.model_class
            #         fields = '__all__'
            # return AddTable

            #type('类名','要继承的类','类下面的字段')
            # meta = type('Meta',(object,),{'model':self.model_class,'fields':'__all__'})
            # type('AddTable',(ModelForm,),{'Meta':meta})


    # 4. 关键字搜索
    show_search_form = False
    '''是否有搜索权限'''
    def get_show_search_form(self):
        return self.show_search_form

    '''搜索字段'''
    search_fields = []
    def get_search_fields(self):
        result = []
        if self.search_fields:
            result.extend(self.search_fields)
        return result

    '''search_key,初始值已经设置,要在前端input name设置一下'''
    '''搜索条件'''
    def get_search_condition(self):
        self.key_word = self.request.GET.get(self.search_key)  #拿到用户输入的关键
        # print('key_word===',self.key_word)
        search_fields = self.get_search_fields() # 例如 : search_fields = ['name__contains', 'email__contains']
        condition = Q()
        condition.connector = 'or'
        if self.key_word and self.get_show_search_form(): # 必须有权限
            for fields_name in search_fields:
                condition.children.append((fields_name,self.key_word))
                #name = 'fei' or email = 'fei'
        return condition

    # 5. 定制
    show_actions = False
    def get_show_actions(self):
        return self.show_actions

    actions = []
    def get_actions(self):
        result = []
        if self.actions:
            result.extend(self.actions)
        return result



    # ############# 处理请求的方法 ################

    def changelist_view(self, request, *args, **kwargs):

        queryset = self.model_class.objects.filter(self.get_search_condition())
        # print('queryset===',queryset)
        cl = ChangeList(self,queryset)
        return render(request, 'stark/changelist.html', {'cl':cl})

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


        '''GET请求显示标签和默认值'''
        if request.method == "GET":
            form = model_form_class(instance=obj)
            return render(request,"stark/change_view.html",{"form":form})
        else:
            form = model_form_class(instance=obj,data=request.POST)
            if form.is_valid:
                form.save()
                '''获取到url?后面的值'''
                list_query_str = request.GET.get(self._query_param_key)
                list_url = '%s?%s'%(self.get_list_url(),list_query_str)
                return redirect(list_url)
            return render(request,"stark/change_view.html",{"form":form})



class StarkSite(object):

    def __init__(self):
        self._registry = {}

    def register(self,model_class,stark_config_class=None):
        if not stark_config_class:
            stark_config_class = StarkConfig

        self._registry[model_class] = stark_config_class(model_class,self)

    def get_urls(self):

        url_pattern = []

        for model_class,stark_config_obj in self._registry.items():
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
        return self.get_urls(),None,"stark"

site = StarkSite()
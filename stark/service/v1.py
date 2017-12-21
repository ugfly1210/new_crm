import copy
from django.conf.urls import url,include
from django.shortcuts import HttpResponse,render,reverse,redirect
from django.utils.safestring import mark_safe
from django.forms import ModelForm
from stark.utils.page import Pagination
from django.http import QueryDict
from django.db.models import Q

class FilterOption:
    def __init__(self,field_name,multi=False,condition=None,is_choice=False): # condition是删选条件,比如我们只想让用户看到非全部部门
        self.field_name = field_name
        self.multi = multi
        self.is_choice = is_choice

        self.condition = condition
    '''接下来的两个函数,就可以通过自定制获取数据库的数据,还可以'''
    # 筛选条件,condition存在在(FK,M2M),注释同condition注释中
    def get_queryset(self,_field):
        if self.condition:
            return _field.rel.to.objects.filter(self.condition)
        return _field.rel.to.objects.all()

    def get_choices(self,_field):
        return _field.choices

class FilterRow(object):
    # def __init__(self,option,data,params):  # params是request.GET那个参数就是querydict对象
    def __init__(self,option,data,request):
        self.data = data
        self.option = option
        self.request = request         # 防止数据变动,使用深拷贝
    def __iter__(self):
        params = copy.deepcopy(self.request.GET) # 用户请求发来的数据
        # 要想动态,就给它设置属性
        params._mutable = True
        current_id = params.get(self.option.field_name)  # 单选
        # 多选
        current_id_list = params.getlist(self.option.field_name)
        '''如果用户请求发来的值,和我循环过程的值一样就表示它被选中,就要加active'''

        #点击全部后,要把后面响应数据去掉
        if self.option.field_name in params:
            del params[self.option.field_name]
        else: # 否则,就是用户并没有选择任何选项,就应该是全部
            url = "{0}?{1}".format(self.request.path_info,params.urlencode())
            yield mark_safe('<a class="active" href="{0}">全部</a>'.format(url))
        '''以下都是处理url,用户点选之后,得到的url'''
        # ((1,'n',2,'nv'))
        for val in self.data:
            if self.option.is_choice:
                pk,text = str(val[0]),val[1] # 这样就表示它是choice选项  ,这里是为了将((1,'男'),(2,'女')) 的id和text拿到
            else: # 它就是一个对象了
                pk,text = str(val.pk),str(val)  # 这里给pk变为字符串是为了和用户发来的curent_id对比,看是否是被选中

            '''单选相关'''
            if not self.option.multi:
                params[self.option.field_name] = pk  # 我只拿我当前field_name对应的值,其他的我不管
                url = "{0}?{1}".format(self.request.path_info,params.urlencode())
                if current_id == pk:
                    yield mark_safe("<a class='active' href='{0}'>{1}</a>".format(url, text))  # 路径获取完成
                else:
                    yield mark_safe("<a href='{0}'>{1}</a>".format(url,text)) # 路径获取完成
            else:
                '''多选相关 current_id_list = ['1','2']'''
                # 如果是多选,要先做判断
                _params = copy.deepcopy(params)
                id_list = _params.getlist(self.option.field_name)

                if pk in current_id_list:
                    id_list.remove(pk)
                    _params.setlist(self.option.field_name,id_list)
                    url = "{0}?{1}".format(self.request.path_info,_params.urlencode())
                    yield mark_safe("<a class='active' href='{0}'>{1}</a>".format(url, text))
                else:
                    id_list.append(pk)
                    # params中被重新赋值
                    _params.setlist(self.option.field_name,id_list)
                    # 创建url
                    url = "{0}?{1}".format(self.request.path_info, _params.urlencode())
                    yield mark_safe("<a href='{0}'>{1}</a>".format(url, text))

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

        # actions批量操作相关
        self.actions = config.get_actions()
        self.show_actions = config.get_show_actions()

        # 组合搜索
        self.comb_filter = config.get_comb_filter()

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

    '''改造actions'''
    def modify_actions(self):
        result = []
        for func in self.actions:
            temp = {'name':func.__name__,'text':func.short_desc} # 拿到函数名
            result.append(temp)
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

    # # 组合搜索 return版本
    # def gen_comb_filter(self):
    #     '''它返回什么,页面就看到什么'''
    #     # comb_filter = ['gender','depart','roles']
    #     data_list = []
    #     # 里面有三个对象.一个是大元祖,两个列表
    #     from django.db.models import ForeignKey,ManyToManyField
    #     for option in self.comb_filter: #option是FilterOption对象
    #         # _field是当前字段
    #         _field = self.model_class._meta.get_field(option.field_name)
    #         # print(field_name,_field.choices)
    #         '''
    #         gender app02.UserInfo.gender
    #         depart app02.UserInfo.depart
    #         roles app02.UserInfo.roles
    #         这是未加choices
    #         '''
    #         '''
    #         gender ((1, '男'), (2, '女'), (3, '少伟'))
    #         depart []
    #         roles []
    #         '''
    #         if isinstance(_field,ForeignKey):
    #             # 获取当前字段depart关联的表,并拿到所有字段. 是FK,
    #             # print(_field.rel) # <ManyToOneRel: app02.userinfo>
    #             # print(_field.rel.to) # <class 'app02.models.Department'>找到关联的表了 通过.objects.all()拿到所有字段
    #             data_list.append( FilterRow(option.get_queryset(_field)) ) # 这里加FilterRow,是为了吧数据封装成FilterRow对象
    #         elif isinstance(_field,ManyToManyField):
    #             # data_list.append( FilterRow(_field.rel.to.objects.all()) )
    #             data_list.append(FilterRow(option.get_queryset(_field)))
    #         else:
    #             data_list.append(FilterRow(option.get_choices(_field)) )
    #     # 拿到所有的数据后,如何让它显示?   前端for循环两次拿得到
    #     return data_list
    # 组合搜索 yield版本
    def gen_comb_filter(self):
        '''生成器函数'''
        '''它返回什么,页面就看到什么'''
        # comb_filter = ['gender','depart','roles']
        # 里面有三个对象.一个是大元祖,两个列表
        from django.db.models import ForeignKey,ManyToManyField
        for option in self.comb_filter: #option是FilterOption对象
            # _field是当前字段
            _field = self.model_class._meta.get_field(option.field_name)
            # print(field_name,_field.choices)
            '''
            gender app02.UserInfo.gender
            depart app02.UserInfo.depart
            roles app02.UserInfo.roles
            这是未加choices
            '''
            if isinstance(_field,ForeignKey):
                # 获取当前字段depart关联的表,并拿到所有字段. 是FK,
                # print(_field.rel) # <ManyToOneRel: app02.userinfo>
                # print(_field.rel.to) # <class 'app02.models.Department'>找到关联的表了 通过.objects.all()拿到所有字段
                row = FilterRow(option,option.get_queryset(_field),self.request)  # 这里加FilterRow,是为了把数据封装成FilterRow对象
            elif isinstance(_field,ManyToManyField):
                # data_list.append( FilterRow(_field.rel.to.objects.all()) )
                row = FilterRow(option,option.get_queryset(_field),self.request)
            else:
                row = FilterRow(option,option.get_choices(_field),self.request)
        # 拿到所有的数据后,如何让它显示?   前端for循环两次拿得到
            yield row  # 可迭代对象, 对应该函数, 为什么它是可迭代对象,应为你看FilterRow. 它有__iter__方法
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

    # 5. 定制批量操作 actions
    show_actions = False
    def get_show_actions(self):
        return self.show_actions

    actions = []
    def get_actions(self):
        result = []
        if self.actions:
            result.extend(self.actions)
        return result

    # 6. 组合搜索
    '''它是在页面上可以看到的,所以找到changelist_view'''
    comb_filter = []
    def get_comb_filter(self):
        result = []
        if self.comb_filter:
            result.extend(self.comb_filter)
        return result

    # ############# 处理请求的方法 ################

    def changelist_view(self, request, *args, **kwargs):

        '''批量actions操作相关'''
        if request.method == 'POST' and self.get_show_actions():
            func_name_str = request.POST.get('list_action')
            # 拿到字符串格式的函数名,通过反射 在self里面找到该函数(跑到stark.py UserInfoConfig里面找到了)
            action_func = getattr(self,func_name_str)
            # 加()执行,手动传进去一个request参数.听话.
            action_func(request)
            pk_list = request.POST.get('pk')
            ### 如果没返回值,就继续往下执行

        # 用户传过来的值,构造搜索条件
        #392 ~ 403 单选操作
        comb_condition = {}
        option_list = self.get_comb_filter()  # 拿到所有的option对象,用于

        for key in request.GET.keys():  # 用key拿值,是因为可能是多选,生成多个值.
            value_list = request.GET.getlist(key)
            flag = False
            for option in option_list:
                if option.field_name == key:
                    flag = True
                    break
                if flag:  # 在的话就构造条件
                    comb_condition["%s__in"%key] = value_list  # {'gender__in':[1],'depart__in':[1,2,]}

        # 搜索相关
        queryset = self.model_class.objects.filter(self.get_search_condition()).filter(**comb_condition).distinct()
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
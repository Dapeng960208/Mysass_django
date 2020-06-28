from django.db import models


# Create your models here.
class UserInfo(models.Model):
    """用户表"""
    username = models.CharField(verbose_name='用户名', max_length=32, db_index=True)
    telephone = models.CharField(verbose_name='手机号', max_length=11)
    email = models.EmailField(verbose_name='邮箱', max_length=24)
    password = models.CharField(verbose_name='密码', max_length=32)


class PricePolicy(models.Model):
    category_choice = ((1, '免费版'), (2, '收费版'), (3, '其他'))
    category = models.SmallIntegerField(verbose_name='收费类型', default=2, choices=category_choice)
    title = models.CharField(verbose_name='标题', max_length=24)
    price = models.PositiveIntegerField(verbose_name='价格')
    project_num = models.PositiveIntegerField(verbose_name='项目数')
    project_member = models.PositiveIntegerField(verbose_name='项目成员')
    project_space = models.PositiveIntegerField(verbose_name='单项目空间（G)')
    per_file_size = models.PositiveIntegerField(verbose_name='单文件大小（M')

    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class Transaction(models.Model):
    """交易记录表：
    支付状态，订单号，用户，价格策略，购买数量，实际支付价格，起始时间，终止时间，创建时间
    """
    status_choice = ((1, '已支付'), (2, '未支付'))
    status = models.SmallIntegerField(verbose_name='支付状态', choices=status_choice)
    order = models.CharField(verbose_name='订单号', max_length=64, unique=True)  # 唯一索引

    user = models.ForeignKey(verbose_name='用户名', to='UserInfo')
    price_policy = models.ForeignKey(verbose_name='价格策略', to='PricePolicy')

    count = models.SmallIntegerField(verbose_name='数量（年）', help_text='0表示无限期')
    price = models.IntegerField(verbose_name='实际支付价格')

    start_time = models.DateTimeField(verbose_name='起始时间', null=True, blank=True)
    end_time = models.DateTimeField(verbose_name='终止时间', null=True, blank=True)
    # 订单生成的创建时间
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class Project(models.Model):
    """ 项目表 """
    COLOR_CHOICES = (
        (1, "#56b8eb"),  # 56b8eb
        (2, "#f28033"),  # f28033
        (3, "#ebc656"),  # ebc656
        (4, "#a2d148"),  # a2d148
        (5, "#20BFA4"),  # #20BFA4
        (6, "#7461c2"),  # 7461c2,
        (7, "#20bfa3"),  # 20bfa3,
    )

    name = models.CharField(verbose_name='项目名', max_length=32)
    color = models.SmallIntegerField(verbose_name='颜色', choices=COLOR_CHOICES, default=1)
    desc = models.CharField(verbose_name='项目描述', max_length=255, null=True, blank=True)

    use_space = models.BigIntegerField(verbose_name='项目已使用空间', default=0, help_text='字节')

    star = models.BooleanField(verbose_name='星标', default=False)

    join_count = models.SmallIntegerField(verbose_name='参与人数', default=1)
    creator = models.ForeignKey(verbose_name='创建者', to='UserInfo')
    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    # 桶对象存储，用来存储用户的图片，上传的文件
    bucket = models.CharField(verbose_name='cos桶', max_length=128)
    region = models.CharField(verbose_name='cos区域', max_length=28)


class ProjectUser(models.Model):
    """ 项目参与者 """
    project = models.ForeignKey(verbose_name='项目', to='Project')
    user = models.ForeignKey(verbose_name='参与者', to='UserInfo')
    star = models.BooleanField(verbose_name='星标', default=False)

    create_datetime = models.DateTimeField(verbose_name='加入时间', auto_now_add=True)


class Wiki(models.Model):
    title = models.CharField(verbose_name='标题', max_length=32)
    content = models.TextField(verbose_name='内容')
    project = models.ForeignKey(verbose_name='项目', to='Project')
    # 自关联
    parent = models.ForeignKey(verbose_name='父文档', to='Wiki', null=True, blank=True, related_name='children')
    depth = models.IntegerField(verbose_name='深度', default=1)

    def __str__(self):
        return self.title


class FileRepository(models.Model):
    """文件库"""
    project = models.ForeignKey(verbose_name='项目', to='Project')
    file_type_choice = (
        (1, '文件'),
        (2, '文件夹')
    )
    file_type = models.SmallIntegerField(verbose_name='文件类型', choices=file_type_choice)
    name = models.CharField(verbose_name='文件名', max_length=128, help_text="文件/文件夹名")
    key = models.CharField(verbose_name="文件存储在cos的KEY", max_length=128, null=True, blank=True)
    file_size = models.IntegerField(verbose_name='文件大小', null=True, blank=True)
    file_path = models.CharField(verbose_name='文件路径', max_length=255, null=True, blank=True)
    update_user = models.ForeignKey(verbose_name='更新者', to='UserInfo')
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    parent_file = models.ForeignKey(verbose_name='父级目录', to='self', related_name='child', null=True, blank=True)


class Issues(models.Model):
    """ 问题 """
    project = models.ForeignKey(verbose_name='项目', to='Project')
    issues_type = models.ForeignKey(verbose_name='问题类型', to='IssuesType')
    module = models.ForeignKey(verbose_name='模块', to='Module', null=True, blank=True)

    subject = models.CharField(verbose_name='主题', max_length=80)
    desc = models.TextField(verbose_name='问题描述')
    priority_choices = (
        ("danger", "高"),
        ("warning", "中"),
        ("success", "低"),
    )
    priority = models.CharField(verbose_name='优先级', max_length=12, choices=priority_choices, default='danger')
    # 新建、处理中、已解决、已忽略、待反馈、已关闭、重新打开
    status_choices = (
        (1, '新建'),
        (2, '处理中'),
        (3, '已解决'),
        (4, '已忽略'),
        (5, '待反馈'),
        (6, '已关闭'),
        (7, '重新打开'),
    )
    status = models.SmallIntegerField(verbose_name='状态', choices=status_choices, default=1)

    assign = models.ForeignKey(verbose_name='指派', to='UserInfo', related_name='task', null=True, blank=True)
    attention = models.ManyToManyField(verbose_name='关注者', to='UserInfo', related_name='observe', blank=True)

    start_date = models.DateField(verbose_name='开始时间', null=True, blank=True)
    end_date = models.DateField(verbose_name='结束时间', null=True, blank=True)
    mode_choices = (
        (1, '公开模式'),
        (2, '隐私模式'),
    )
    mode = models.SmallIntegerField(verbose_name='模式', choices=mode_choices, default=1)

    parent = models.ForeignKey(verbose_name='父问题', to='self', related_name='child', null=True, blank=True,
                               on_delete=models.SET_NULL)

    creator = models.ForeignKey(verbose_name='创建者', to='UserInfo', related_name='create_problems')

    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    latest_update_datetime = models.DateTimeField(verbose_name='最后更新时间', auto_now=True)

    def __str__(self):
        return self.subject


class Module(models.Model):
    """ 模块（里程碑）"""
    project = models.ForeignKey(verbose_name='项目', to='Project')
    title = models.CharField(verbose_name='模块名称', max_length=32)

    def __str__(self):
        return self.title


class IssuesType(models.Model):
    """ 问题类型 例如：任务、功能、Bug """

    PROJECT_INIT_LIST = ["任务", '功能', 'Bug']

    title = models.CharField(verbose_name='类型名称', max_length=32)
    project = models.ForeignKey(verbose_name='项目', to='Project')

    def __str__(self):
        return self.title

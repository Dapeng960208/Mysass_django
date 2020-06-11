from django import forms
from app01.forms.bootstrap import BootstrapForm
from app01 import models
from django.core.exceptions import ValidationError
from app01.forms.widgets import ColorRadioSelect


class ProjectModelForm(BootstrapForm, forms.ModelForm):
    bootstarp_class_exclude = ['color']

    class Meta:
        model = models.Project
        fields = ['name', 'color', 'desc']
        widgets = {
            'desc': forms.Textarea,
            'color': ColorRadioSelect(attrs={'class': 'color-radio'}),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_name(self):
        """
        局部钩子：
        1.验证该用户是否创建过相同的项目
        2,额度是否够创建一个新项目
        """
        name = self.cleaned_data['name']
        exists = models.Project.objects.filter(name=name, creator=self.request.userInfo.user).exists()
        if exists:
            raise ValidationError('项目已存在，请勿重复创建')

        max_num = self.request.userInfo.price_policy.project_num
        exist_num = models.Project.objects.filter(creator=self.request.userInfo.user).count()
        if exist_num > max_num:
            raise ValidationError('创建项目已达上限,请购买套餐')

        return name

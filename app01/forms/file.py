from django import forms
from app01 import models
from app01.forms.bootstrap import BootstrapForm
from django.core.exceptions import ValidationError


class FileModelFOrm(BootstrapForm, forms.ModelForm):
    class Meta:
        model = models.FileRepository
        fields = ['name']

    def __init__(self, request, parent_obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.parent_obj = parent_obj

    def clean_name(self):
        """验证同一目录下文件夹是否重名"""
        name = self.cleaned_data['name']
        queryset = models.FileRepository.objects.filter(file_type=2, name=name,
                                                        project=self.request.userInfo.project)
        if self.parent_obj:
            exists = queryset.filter(parent_file=self.parent_obj).exists()
        else:
            exists = queryset.filter(parent_file__isnull=True).exists()
        if exists:
            raise ValidationError('文件夹已存在')
        return name

from app01 import models
from django import forms
from app01.forms.bootstrap import BootstrapForm


class WikiModelForm(BootstrapForm, forms.ModelForm):
    class Meta:
        model = models.Wiki
        exclude = ['project', 'depth']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 不选择父文章就选择空
        total_data_list = [("", "无"), ]
        data_list = models.Wiki.objects.filter(project=request.userInfo.project).values_list('id', 'title')
        total_data_list.extend(data_list)

        self.fields['parent'].choices = total_data_list

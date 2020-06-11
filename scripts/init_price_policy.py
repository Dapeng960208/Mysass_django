import base

from app01 import models


def run():
    """离线脚本，用来创建免费版的价格策略"""
    exists = models.PricePolicy.objects.filter(category=1, title='免费版').exists()
    if not exists:
        models.PricePolicy.objects.create(
            category=1,
            title='免费版',
            price=0,
            project_num=3,
            project_member=2,
            project_space=20,
            per_file_size=5,
        )


if __name__ == '__main__':
    run()

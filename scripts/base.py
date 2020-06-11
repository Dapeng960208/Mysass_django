import os, sys, django

# 获取当前路径，并将当前路径加载到django路径中
basic_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(basic_dir)
# 从Sass.settings 加载配置文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sass.settings')
# 模拟启动django
django.setup()

from django.shortcuts import render

def dashboard(request,project_id):
    return render(request,'dashboard.html')


def issues(request,project_id):
    return render(request,'issues.html')

def statistics(request,project_id):
    return render(request,'statistics.html')


def file(request,project_id):
    return render(request,'file.html')




def settings(request,project_id):
    return render(request,'settings.html')
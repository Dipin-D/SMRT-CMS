from django.shortcuts import render, redirect

def demo(request):
    return render(request, 'demo.html')

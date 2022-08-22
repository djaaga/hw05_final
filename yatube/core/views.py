from django.shortcuts import render


def handler404(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def handler403(request, reason=''):
    return render(request, 'core/403csrf.html', status=403)


def handler500(request, *args, **kwargs):
    return render(request, 'core/500.html', status=500)

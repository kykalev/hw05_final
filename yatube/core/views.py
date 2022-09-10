from django.shortcuts import render


def page_not_found(request, exception):
    """Вывод кастомной страны ошибки 404."""
    # Переменная exception содержит отладочную информацию;
    # выводить её в шаблон пользовательской страницы 404 мы не станем
    template = 'core/404.html'
    context = {'path': request.path}
    return render(request, template, context, status=404)


def csrf_failure(request, reason=''):
    """Вывод кастомной страны ошибки 403."""
    template = 'core/403.html'
    return render(request, template, status=403)


def internal_server_error(request):
    """Вывод кастомной страны ошибки 500."""
    template = 'core/500.html'
    context = {'path': request.path}
    return render(request, template, context, status=500)

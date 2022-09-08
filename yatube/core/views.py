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
    template = 'core/403csrf.html'
    return render(request, template)

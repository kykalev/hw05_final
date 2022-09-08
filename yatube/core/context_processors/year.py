from datetime import date


def year(request):
    """Добавляет переменную с текущим годом."""
    year = date.today()
    return {
        'year': year.year,
    }

# Проект «Проект hw05_final»
## Описание
Проект hw05_final - мини социальная сеть. Создана возможность зарегистрироваться пользователю, Оставлять посты с картинкой. Можно подписываться/отписываться на другого пользователя. Можно выбрать группу(из предложенных) к которому принадлежит пост. Группу может создать администратор.

## Использованные технологии
В проекте использованы технологии:

Python==3.7.9  
Django==2.2.16  
mixer==7.1.2  
Pillow==8.3.1  
pytest==6.2.4  
pytest-django==4.4.0  
pytest-pythonpath==0.7.3  
requests==2.26.0  
six==1.16.0  
sorl-thumbnail==12.7.0  
Faker==12.0.1  


## Установка
Клонировать репозиторий и перейти в него в командной строке:

```commandline
git clone https://github.com/kykalev/hw05_final.git
```

```commandline
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```commandline
python -m venv venv
```

```commandline
source venv/Scripts/activate
```

```commandline
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```commandline
pip install -r requirements.txt
```

Выполнить миграции:

```commandline
python manage.py migrate
```

Запустить проект:

```commandline
python manage.py runserver
```

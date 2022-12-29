# ximc_device
Python-обертка для работы с контроллерами шаговых двигателей с помощью библиотеки [libximc](https://pypi.org/project/libximc/).

## Запуск примера на Jupyter Notebook

1. Установите необходимые зависимости. Для этого перейдите в папкy **scripts** и выполните скрипт:
   - **install_for_py_36_37.bat**, если вы работаете в *Windows* с *Python* версии 3.6-3.7;
   - **install_for_py_38_311.bat**, если вы работаете в Windows с *Python* версии 3.8-3.11;
   - **install_for_py_36_37.sh**, если вы работаете в *Linux* с *Python* версии 3.6-3.7;
   - **install_for_py_38_311.sh**, если вы работаете в *Linux* с *Python* версии 3.8-3.11.
   
2. В командной строке перейдите в папку **scripts** и выполните команду
   - если вы работаете в *Windows*:
   
     ```bash
     venv\Scripts\python -m jupyter notebook jupyter_demo.ipynb
     ```
   
   - если вы работаете в *Linux*:
   
     ```bash
     venv/bin/python3 -m jupyter notebook jupyter_demo.ipynb
     ```
   
3. Далее следуйте инструкции из примера **jupyter_demo.ipynb**.

## Запуск примера на Google Colab

1. Откройте в браузере [Google Colab](https://colab.research.google.com/).

2. В появившемся окошке выберите "Загрузить" и выберите файл **jupyter_demo.ipynb**.

   ![1](./data/1.png)

3. Далее следуйте инструкции из примера **jupyter_demo.ipynb**.

## Примечание

Работа приложения была проверена на следующих машинах:

- *Windows 10*, *Python 3.6.8* (64 bit), *3.7.9* (64 bit), *3.8.10* (64 bit), *3.9.13* (64 bit), *3.10.7* (64 bit), *3.11.1* (64 bit). Имеется проблема установки Jupyter Notebook на 32 bit *Python* (о проблеме можно почитать, например, [здесь](https://stackoverflow.com/questions/67343397/how-to-fix-errors-occurring-on-installation-of-jupyter-notebook)). Поэтому для работы нужно использовать *Python* 64 bit;
- *Ununtu 18.04*, *Python 3.6.9*;
- *Ubuntu 20.04*, *Python 3.8.10*.

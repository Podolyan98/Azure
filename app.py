from flask import Flask, render_template, request, send_from_directory, redirect
from flask_pymongo import PyMongo
from flask_paginate import Pagination, get_page_args
from flask_mail import Mail, Message
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.web import WebSiteManagementClient
import subprocess
import json
import pandas as pd
import bson
import smtplib
import logging


app = Flask(__name__)
"""подключение к базе данных"""
app.config["MONGO_URI"] = " "
mongo = PyMongo(app)

"""конфигурация для отправки email"""
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_DEFAULT_SENDER'] = ''
app.config['MAIL_PASSWORD'] = ''
mail = Mail(app)

"""cтартовая страница"""
@app.route('/')
def faq():
    return render_template('faq.html')

"""загрузка одной из вкладок для запуска пауков"""
@app.route('/<page_id>', methods=['GET', 'POST'])
def page(page_id):
    """page_id - аргумент для определения шаблона, паука и файла настроек"""
    file_html = f"{page_id}.html"
    file_py = f"{page_id}.py"
    file_json = f"{page_id}.json"

    if request.method == 'POST':
        """получение аргументов"""
        specialty = request.form.getlist('specialty[]')
        state = request.form.getlist('state[]')
        city = request.form.getlist('city[]')
        email = request.form.getlist('email[]')
        
        """запись аргументов в файл"""
        settings = ''
        with open('settings/' + file_json, 'r') as f:
            for line in f.read():
                settings += line
        
        settings = json.loads(settings)
        settings['specialty'] = specialty
        settings['state'] = state
        settings['city'] = city
            
        with open('settings/' + file_json, 'w') as f:
            f.write(json.dumps(settings, indent=4))

        """запуск подпроцесса"""
        process = subprocess.Popen('python spiders/' + file_py, shell = True)
        process.wait()

        """отправка email"""
        if email != []:
            try:
                msg = Message('Scraper', recipients = email)
                msg.body = 'Web-scraper https://<app-name>.azurewebsites.net/%s has finished collecting information!' % page_id
                mail.send(msg)
            except smtplib.SMTPException as error:
                logging.exception(error)
    try:
        """загрузка документов из базы данных"""
        cards = [card for card in mongo.db[page_id].find()]
        """создание пагинации"""
        total = len(cards)
        page, per_page, offset = get_page_args(page_parameter = 'page', 
                                               per_page_parameter = 'per_page')
        pagination = Pagination(page = page, 
                                per_page = per_page, 
                                total = total, 
                                css_framework = 'bootstrap4')
        """загрузка страницы"""
        return render_template(file_html, cards = cards[offset: offset + per_page], 
                                          page = page, 
                                          per_page = per_page, 
                                          pagination = pagination, 
                                          len = len)
    except:
        """исключение, если нет документов в коллекции"""
        return render_template(file_html)

"""перезапуск приложения"""
@app.route('/restart/app')
def restart_app():
    """элементы службы для аутентификации"""
    subscription_id = ""
    client_id = ""
    secret = ""
    tenant = ""

    """аутентификация клиента"""
    credentials = ServicePrincipalCredentials(client_id = client_id, 
                                              secret = secret, 
                                              tenant = tenant)

    web_client = WebSiteManagementClient(credentials, subscription_id)
    """название группы ресурсов и приложения"""
    web_client.web_apps.restart("<resourceGroup_name>","<web_app_name>") 
    return render_template('faq.html')

"""загрузка профиля"""
@app.route('/profile/<page_id>/<_id>')
def profile(page_id, _id):
    """page_id - аргумент для определения шаблона и коллекции"""
    file_html = f"profile_{page_id}.html"
    """поиск документа в базе данных по id"""
    card = mongo.db[page_id].find_one({"_id": bson.ObjectId(oid=str(_id))})

    if card is None:
        return redirect('/' + page_id)

    return render_template(file_html, card = card)

"""удаление профиля"""
@app.route('/delete/<page_id>/<_id>')
def delete(page_id, _id):
    """удаление документа в базе данных по id, 
       page_id - аргумент для определения коллекции"""
    mongo.db[page_id].delete_one({"_id": bson.ObjectId(oid=str(_id))})
    return redirect(request.referrer)

"""удаление коллекции"""
@app.route('/remove/<page_id>')
def remove(page_id):
    """page_id - аргумент для определения коллекции"""
    mongo.db[page_id].drop()
    return redirect('/' + page_id)

"""экспорт данных их коллекции в формате csv"""
@app.route('/download/<page_id>') 
def get_csv(page_id):
    """page_id - аргумент для определения шаблона и коллекции"""
    file_csv = f"{page_id}.csv"
    query = {}
    """запрос к коллекции"""
    cursor = mongo.db[page_id].find(query)
    """создание DataFrame"""
    df =  pd.DataFrame(list(cursor))
    df.to_csv(file_csv, ';')

    if df.empty == True:
        return redirect('/' + page_id)

    """отправка csv-файла c сервера"""
    return send_from_directory(directory = '', 
                               filename = file_csv, 
                               as_attachment = True, 
                               cache_timeout = 0)
    
"""точка входа"""
if __name__ == '__main__':
    app.run(debug=True, threaded=True) # режим разработчика
    # app.run() 

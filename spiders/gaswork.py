from scrapy.crawler import CrawlerProcess
import scrapy
import json
import pymongo
from pymongo import MongoClient

"""обработка HTTP-запросов/ответов"""
class Gaswork(scrapy.Spider):
    """имя паука"""
    name = 'gaswork'
    """допустимый домен"""
    allowed_domains = ['gaswork.com']

    """настройки"""
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36 OPR/60.0.3255.50747 OPRGX/60.0.3255.50747',
        'DOWNLOAD_DELAY': 0.25,
    }

    """отправка начальных запросов"""
    def start_requests(self): 
        """получение аргументов"""
        settings = ''

        with open('settings/gaswork.json', 'r') as f:
            for line in f.read():
                settings += line
        
        settings = json.loads(settings)

        """формирование ссылок и отправка запросов"""
        for specialty in settings['specialty']:
           yield scrapy.Request('https://www.gaswork.com/search/%s/CV/All' % specialty, callback=self.profile_link)
    
    """получение ссылок на профили"""
    def profile_link(self, response):
        for a in response.css('.center a'):
            yield response.follow(a, callback=self.profile)

        """обработка пагинации"""
        next_page = response.css('.on~ a+ a::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.profile_link)

    """получение информации со страницы профиля"""
    def profile(self, response): 
        """определение таблиц"""
        form0 = response.css('.dynamic-form')[0]
        form1 = response.css('.dynamic-form')[1]
        form2 = response.css('.dynamic-form')[2]
        form3 = response.css('.dynamic-form')[3]
        form4 = response.css('.dynamic-form')[4]
        form5 = response.css('.dynamic-form')[5]
        form6 = response.css('.dynamic-form')[6]
        form7 = response.css('.dynamic-form')[7]
        form8 = response.css('.dynamic-form')[8]

        """запись в словарь"""
        item = {
            'url' : response.request.url,
            
            # CONTACT INFORMATION
            'Company_Name': form0.css('#fq9 td::text')[1:].getall(),
            'Anesthesiologists_Name': form0.css('#fq14 td::text')[1:].getall(),
            'Contact_Name': form0.css('#fq61 td::text')[1].get(),
            'Contact_Street_Address_1': form0.css('#fq128 td::text')[1:].getall(),
            'Contact_Street_Address_2': form0.css('#fq489 td::text')[1:].getall(),
            'Contact_City': form0.css('#fq23 td::text')[1].get(),
            'Contact_State': form0.css('#fq358 td::text')[1:].getall(),
            'Contact_Zip_Code': form0.css('#fq28 td::text')[1:].getall(),
            'Contact_Country': form0.css('#fq357 td::text')[1:].getall(),
            'Contact_Voice_Phone': form0.css('#fq26 td::text')[1:].getall(),
            'Contact_Fax': form0.css('#fq25 td::text')[1:].getall(),
            'Contact_Web_Site' : form0.css('#fq27 td::text')[1:].getall(),
            'Preferred_Contact_Method': form0.css('#fq392 td::text')[1:].getall(),

            # POSITION DESIRED
            'fq485' : form1.css('#fq485 td::text')[1].get(),
            'fq419' : form1.css('#fq419 td::text')[1:].getall(),
            'fq411' : form1.css('#fq411 td::text')[1:].getall(),
            'fq470' : form1.css('#fq470 td::text')[1:].get(),
            'fq426' : form1.css('#fq426 td::text')[1:].get(),
            'fq374' : form1.css('#fq374 td::text').get(),

            # # QUALIFICATIONS
            'fq442' : form2.css('#fq442 td::text')[1:].getall(),

            # #POSITION DESIRED
            'fq211' : form3.css('#fq211 td::text')[1].get(),
            'fq212' : form3.css('#fq212 td::text')[1].get(),
            'fq362' : form3.css('#fq362 td::text')[1].get(),
            'fq209' : form3.css('#fq209 td::text')[1].get(),
            'fq385' : form3.css('#fq385 td::text')[1].get(),
            'fq168' : form3.css('#fq168 td::text')[2].get(),
            'fq164' : form3.css('#fq164 td::text')[2].get(),
            'fq169' : form3.css('#fq169 td::text')[1].get(),
            'fq387' : form3.css('#fq387 td::text')[1].get(),
            'fq386' : form3.css('#fq386 td::text')[2].get(),
            'fq376' : form3.css('#fq376 td::text')[2].get(),
            'fq171' : form3.css('#fq171 td::text')[1].get(),
            'fq166' : form3.css('#fq166 td::text')[1].get(),
            'fq167' : form3.css('#fq167 td::text')[1].get(),
            'fq165' : form3.css('#fq165 td::text')[1].get(),
            'fq354' : form3.css('#fq354 td::text')[1].get(),
            'fq396' : form3.css('#fq396 td::text')[1].get(),
            'fq390' : form3.css('#fq390 td::text')[1].get(),
            'fq210' : form3.css('#fq210 td::text')[1].get(),

            # # SALARY AND INCOME INFORMATION
            'fq399' : form4.css('#fq399 td::text')[3].get(),
            'fq494' : form4.css('#fq494 td::text')[4].get(),
            'fq214' : form4.css('#fq214 td::text')[1].get(),
            'fq213' : form4.css('#fq213 td::text')[1].get(),
            'fq218' : form4.css('#fq218 td::text')[1].get(),
            'fq172' : form4.css('#fq172 td::text')[1].get(),
            'fq170' : form4.css('#fq170 td::text')[1].get(),

            # QUALIFICATIONS
            'fq405' : form5.css('#fq405 td::text')[1].get(),
            'fq176' : form5.css('#fq176 td::text')[1].get(),
            'fq11' : form5.css('#fq11 td::text')[1].get(),
            'fq15' : form5.css('#fq15 td::text')[1].get(),
            'fq375' : form5.css('#fq375 td::text')[1].get(),
            'fq120' : form5.css('#fq120 td::text')[1].get(),
            'fq161' : form5.css('#fq161 td::text')[1].get(),
            'fq119' : form5.css('#fq119 td::text')[1].get(),
            'fq127' : form5.css('#fq127 td::text')[1].get(),
            'fq181' : form5.css('#fq181 td::text')[1].get(),
            'fq162' : form5.css('#fq162 td::text')[1].get(),
            'fq406' : form5.css('#fq406 td::text')[1:].getall(),
            'fq513' : form5.css('#fq513 td::text')[1].get(),

            # CURRENT EMPLOYER
            'fq34' : form6.css('#fq34 td::text')[1].get(),
            'fq130' : form6.css('#fq130 td::text')[1:].getall(),
            'fq126' : form6.css('#fq126 td::text')[1].get(),

            # OTHER
            'fq13' : form7.css('#fq13 td::text')[1].get(),
            'fq67' : form7.css('#fq67 td::text').get(),
            'fq97' : form7.css('#fq97 td::text')[1].get(),
            'fq98' : form7.css('#fq98 td::text')[1].get(),
            'fq443' : form7.css('#fq443 td::text')[1].get(),

            # POST INFORMATION
            'Date_Posted' : form8.css('.answer::text')[0].get(),
            'Last_Updated' : form8.css('.answer::text')[1].get(),
            'Posted_By' : form8.css('.answer::text')[2].get(),
            'Reference' : form8.css('.answer::text')[3].get(),
            'Priority' : form8.css('.answer::text')[4].get(),
            'Section' : form8.css('.answer::text')[5].get(),
            'Form_Type' : form8.css('.answer::text')[6].get(),
            'User_Type' : form8.css('.answer::text')[7:].getall(),
            }

        """подключение к базе данных и запись словаря"""
        cluster = pymongo.MongoClient(" ") # строка подключения
        db = cluster.Profiles # название базы данных
        collection = db.gaswork # название коллекции
        collection.insert_one(item) # запись словаря
        
"""точка входа"""
if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(Gaswork)
    process.start()
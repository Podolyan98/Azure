from scrapy.crawler import CrawlerProcess
from pymongo import MongoClient
import scrapy
import json
import pymongo

"""обработка HTTP-запросов/ответов"""
class Ratemds(scrapy.Spider):
    """имя паука"""
    name = 'ratemds'
    """допустимый домен""" 
    allowed_domains = ['ratemds.com']
    """настройки"""
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36 OPR/60.0.3255.50747 OPRGX/60.0.3255.50747',
        'DOWNLOAD_DELAY': 2.5,
    }

    """отправка начальных запросов"""
    def start_requests(self):
        """получение аргументов""" 
        settings = ''
        
        with open('settings/ratemds.json', 'r') as f:
            for line in f.read():
                settings += line
        
        settings = json.loads(settings)

        """формирование ссылок и отправка запросов"""
        if settings['state'] == []:
            for specialty in settings['specialty']:
                yield scrapy.Request('https://www.ratemds.com/best-doctors/?specialty=%s' % specialty, callback=self.profile_link)

        elif settings['city'] == []:
            for specialty in settings['specialty']:
                for state in settings['state']:
                    yield scrapy.Request('https://www.ratemds.com/best-doctors/%s/?specialty=%s' % (state, specialty), callback=self.profile_link)
        else:
            for specialty in settings['specialty']:
                for state in settings['state']:
                    for city in settings['city']:
                        yield scrapy.Request('https://www.ratemds.com/best-doctors/%s/%s/%s' % (state, city, specialty), callback=self.profile_link) 
    
    """получение ссылок на профили"""
    def profile_link(self, response):
        for a in response.css('.search-item-doctor-link'):
            yield response.follow(a, callback=self.profile)

        """обработка пагинации"""    
        next_page = response.css('.pagination-sm a::attr(href)')[-1].get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.profile_link)
            
    """получение информации со страницы профиля"""
    def profile(self, response):
        """получение json"""
        json_data = json.loads(response.xpath("//script[@type='application/ld+json']/text()").get())

        """парсинг json"""
        if json_data['aggregateRating']['ratingCount']:
            try:
                Reviews = json_data['aggregateRating']['ratingCount']
                Phone =  json_data['telephone']
                Address = json_data['address']
            except:
                Reviews = ''
                Phone = ''
                Address = ''
        
        """запись в словарь"""
        item =  {
            'url': response.request.url,
            'Image': json_data['image'],
            'First_and_Last_Name': json_data['name'],
            'Reviews': Reviews,
            'Phone': Phone,
            'Address': Address,
            }

        """подключение к базе данных и запись словаря"""
        cluster = pymongo.MongoClient(" ") # строка подключения
        db = cluster.Profiles # название базы данных
        collection = db.ratemds # название коллекции
        collection.insert_one(item) # запись словаря
        
"""точка входа"""
if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(Ratemds)
    process.start()
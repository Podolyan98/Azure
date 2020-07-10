from scrapy.crawler import CrawlerProcess
from pymongo import MongoClient
import scrapy
import json
import pymongo
import w3lib.url
from urllib.parse import urljoin

"""обработка HTTP-запросов/ответов"""
class Healthgrades(scrapy.Spider):
    """имя паука"""
    name = 'healthgrades'
    """допустимый домен""" 
    allowed_domains = ['healthgrades.com']
    """настройки"""
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36 OPR/60.0.3255.50747 OPRGX/60.0.3255.50747',
        'DOWNLOAD_DELAY': 2.5,
    }

    """отправка начальных запросов"""
    def start_requests(self): 
        """получение аргументов"""
        settings = ''
        
        with open('settings/healthgrades.json', 'r') as f:
            for line in f.read():
                settings += line
        
        settings = json.loads(settings)

        """формирование ссылок и отправка запросов"""
        if settings['state'] == []:
            for specialty in settings['specialty']:
                yield scrapy.Request('https://www.healthgrades.com/api3/usearch?&distances=National' +
                                     '&sort.provider=bestmatch&source=init&what='+ specialty.replace("-", " ") +'&category=provider&cid&debug=false&d' + 
                                     'ebugParams=false&isPsr=false&isFsr=false&isFirstRequest=true&userLocalTime=23%3A55', 
                                      callback=self.pagination)

        elif settings['city'] == []:
            for specialty in settings['specialty']:
                for state in settings['state']:
                    yield scrapy.Request('https://www.healthgrades.com/api3/usearch?where='+ state.split('-')[0] +
                                         '&sort.provider=bestmatch&source=init&what='+ specialty.replace("-", " ") +'&category=provider&cid&debug=false&d' + 
                                         'ebugParams=false&isPsr=false&isFsr=false&isFirstRequest=true&userLocalTime=23%3A55', 
                                          callback=self.pagination)
        else:
            for specialty in settings['specialty']:
                for state in settings['state']:
                    for city in settings['city']:
                        yield scrapy.Request('https://www.healthgrades.com/%s-directory/%s/%s' % (specialty, state, city), callback=self.profile_link_city)
    
    """обработка пагинации"""
    def pagination(self, response):
        """получение json"""
        jsonresponse = json.loads(response.body_as_unicode())
        """парсинг json"""
        totalPages = jsonresponse['search']['searchResults']['totalPages']

        """формирование ссылок с номерами страниц"""
        for page in range(0, totalPages):
            url = w3lib.url.add_or_replace_parameter(response.request.url, 'pageNum', page) 
            yield scrapy.Request(url, callback=self.profile_link)

    """получение ссылок на профили"""
    def profile_link(self, response):
        """получение json"""
        jsonresponse = json.loads(response.body_as_unicode())
        """парсинг json"""
        providerUrl = [i['providerUrl'] for i in jsonresponse['search']['searchResults']['provider']['results']]

        """формирование ссылок на профили"""
        for url in providerUrl:
            url = urljoin('https://www.healthgrades.com', url)
            yield scrapy.Request(url, callback=self.profile)

    """получение ссылок на профили для городов"""
    def profile_link_city(self, response):
        for a in response.css('.provider-name__lnk'): 
            yield response.follow(a, callback=self.profile)

        """обработка пагинации"""
        next_page = response.css('._3ZWfj::attr(href)')[-1].get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.profile_link_city)
            

    def profile(self, response):
        """запись в словарь"""
        item =  {
            'url' : response.request.url,
            'Image' : response.css('.summary-provider-image::attr(src), .designated-provider-image::attr(src)').get(),
            'First_and_Last_Name': response.css('h1::text').get(),
            'Reviews': response.css('.star-reviews-count::text').get(),
            'Gender' : response.css('h1+ div span:nth-child(2)::text, #summary-section p span:nth-child(2)::text').getall(),
            'Phone' : response.css('.toggle-phone-number-button::text, .toggle-phone-number-button::text').get(), # js запрос
            'Address': response.css('.location-row-address::text').getall(),
            'Experience_Check': response.css('.frequency-content-row::text').getall(),
            'Average_Reported_Wait_Time': response.css('.c-pes-wait-time li::text').get(), 
            'Trustworthiness': len(response.css('.c-pes-wait-time+ .c-pes-officestaff-performance li:nth-child(1) .hg3-i-star-full'))/2,
            'Explains_condition_well': len(response.css('.c-pes-wait-time+ .c-pes-officestaff-performance li:nth-child(2) .hg3-i-star-full'))/2,
            'Answer_questions': len(response.css('.c-pes-wait-time+ .c-pes-officestaff-performance li:nth-child(3) .hg3-i-star-full'))/2,
            'Time_well_spent': len(response.css('li:nth-child(4) .hg3-i-star-full'))/2,
            'Scheduling': len(response.css('.c-pes-officestaff-performance+ .c-pes-officestaff-performance li:nth-child(1) .hg3-i-star-full'))/2,
            'Office_environment': len(response.css('.c-pes-officestaff-performance+ .c-pes-officestaff-performance li:nth-child(2) .hg3-i-star-full'))/2,
            'Staff_friendliness': len(response.css('.c-pes-officestaff-performance+ .c-pes-officestaff-performance li~ li+ li .hg3-i-star-full'))/2,
            'Biography': response.css('#learn-bio span::text').getall(),
            'Specialties': response.css('.about-me-specialties .about-me-listitem::text').getall(),         
            'Board_Certifications': response.css('.about-me-board-certifications .about-me-listitem::text').getall(),
            'Education': response.css('.education-card-content div::text').getall(),
            'Awards': response.css('.about-me-awards .about-me-listitem::text').getall(),
            'Comments': response.css('.c-single-comment__comment::text, .c-single-comment__commenter-info span::text').getall()
            }

        """подключение к базе данных и запись словаря"""
        cluster = pymongo.MongoClient(" ") # строка подключения
        db = cluster.Profiles # название базы данных
        collection = db.healthgrades # название коллекции
        collection.insert_one(item) # запись словаря
        
"""точка входа"""
if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(Healthgrades)
    process.start()
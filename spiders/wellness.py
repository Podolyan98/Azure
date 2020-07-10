from scrapy.crawler import CrawlerProcess
from pymongo import MongoClient
import scrapy
import json
import pymongo

"""обработка HTTP-запросов/ответов"""
class Wellness(scrapy.Spider):
    """имя паука"""
    name = 'wellness'
    """допустимый домен""" 
    allowed_domains = ['wellness.com'] 
    """настройки"""
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36 OPR/60.0.3255.50747 OPRGX/60.0.3255.50747',
        'DOWNLOAD_DELAY': 0.5,
    }

    """отправка начальных запросов"""
    def start_requests(self): 
        """получение аргументов"""
        settings = ''
        
        with open('settings/wellness.json', 'r') as f:
            for line in f.read():
                settings += line
        
        settings = json.loads(settings)

        """формирование ссылок и отправка запросов"""
        if settings['state'] == []:
            for specialty in settings['specialty']:
                yield scrapy.Request('https://www.wellness.com/find/%s' % specialty, callback=self.state)

        elif settings['city'] == []:
            for specialty in settings['specialty']:
                for state in settings['state']:
                    yield scrapy.Request('https://www.wellness.com/find/%s/%s' % (specialty, state), callback=self.city)
        else:
            for specialty in settings['specialty']:
                for state in settings['state']:
                    for city in settings['city']:
                        yield scrapy.Request('https://www.wellness.com/find/%s/%s/%s' % (specialty, state, city), callback=self.profile_link)  
    
    """получение ссылок на штаты"""
    def state(self, response):
        for a in response.css('.find-item-container a'):
            yield response.follow(a, callback=self.city)
         
    """получение ссылок на города"""
    def city(self, response):
        for a in response.css('.categories-li a'):
            yield response.follow(a, callback=self.profile_link)
            
    """получение ссылок на профили"""
    def profile_link(self, response):
        for a in response.css('.link'):
            yield response.follow(a, callback=self.profile)

        """обработка пагинации"""
        next_page = response.css('.pagination-next .pagination-link::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.profile_link)

    """получение информации со страницы профиля"""
    def profile(self, response):
        services = response.xpath('.//span[contains(text(),"Services")]')
        education = response.xpath('.//span[contains(text(),"Education")]')
        training = response.xpath('.//span[contains(text(),"Training")]')

        """запись в словарь"""
        item = {
            'url' : response.request.url,
            'Image' : response.css('.listing-photo img::attr(src)').get(),
            'First_and_Last_Name' : response.css('h1::text').get(),
            'About' : response.css('.listing-about::text').getall(),
            'Services' : services.xpath('following-sibling::span[1]/text()').extract(), 
            'Primary_Specialty' : response.css('.normal::text').get(),
            'Practice' : response.css('.years-in-service::text').get(),
            'Education' : education.xpath('following-sibling::span[1]/text()').extract(),
            'Training' : training.xpath('following-sibling::span[1]/text()').extract()
        }       

        """переход на вкладку Reviews"""
        review_link = response.css('#reviews_tab a::attr(href)').get()
        if review_link is not None:
            yield scrapy.Request(response.urljoin(review_link), callback=self.parse_reviews, 
                                                                meta={'item': item})
        else:
            item['Consumer_Feedback'] = ''
            item['Reviews'] = ''
            """переход на вкладку Phone Numbers&Directions"""
            directions_link = response.css('#directions_tab a::attr(href)').get()
            yield scrapy.Request(response.urljoin(directions_link), callback=self.parse_directions, 
                                                                    meta={'item': item})

    """получение информации с вкладки Reviews"""
    def parse_reviews(self, response):
        item = response.meta['item']
        item['Consumer_Feedback'] = response.css('.item-rating-container a::text').get()
        Reviews = response.css('.listing-review-text::text, .blurred.read-more::text, ' +
                               '.response-question::text, .response-answer::text, .review_name::text').getall()   
        """удаление пробелов"""
        item['Reviews'] = [i.strip() for i in Reviews]
        """переход на вкладку Phone Numbers&Directions""" 
        directions_link = response.css('#directions_tab a::attr(href)').get()
        yield scrapy.Request(response.urljoin(directions_link), callback=self.parse_directions, 
                                                                meta={'item': item})

    """получение информации с вкладки Phone Numbers&Directions"""
    def parse_directions(self, response):
        item = response.meta['item']
        item['Phone'] = response.css('.tel::text').get()
        item['Address'] = response.css('.item-separator+ span::text').get()
        
        """подключение к базе данных и запись словаря"""
        cluster = pymongo.MongoClient(" ") # строка подключения
        db = cluster.Profiles # название базы данных
        collection = db.wellness # название коллекции
        collection.insert_one(item) # запись словаря
        
"""точка входа"""
if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(Wellness)
    process.start()
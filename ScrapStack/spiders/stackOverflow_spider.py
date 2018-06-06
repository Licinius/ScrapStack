import scrapy
import json

class StackOverflowSpider(scrapy.Spider):
    '''
    Spider for stack overflow .com

    Attributes:
        name (str): Name of the spider.

    '''
    name = "stack_overflow"
    def start_requests(self):
        '''
        First function fired with 'scrapy crawl stack_overflow'
        Args :
            *kwargs : url to scrap

        Yields :
            Request: the request to download the page 
        '''
        DEFAULT_URL = 'https://stackoverflow.com/questions/13687346/java-hashmap-get-method-null-pointer-exception'
        KEY_URL = 'url' #Constant for the key url
        url = getattr(self,KEY_URL,None)
        if(url is None) :
            url = DEFAULT_URL
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        '''
        Function fired when the page is download
        Args :
            response : object which travels back to the spider that issued the request.

        '''
        self.log("----Start---- ")


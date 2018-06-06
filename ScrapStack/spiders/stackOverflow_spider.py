import scrapy
import json
class StackOverflowSpider(scrapy.Spider):
    '''
    Spider for stack overflow .com

    Attributes:
        name (str): Name of the spider.
    '''
    name = 'stack_overflow'
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
        url = getattr(self,KEY_URL,None) #Get the url passed
        if(url is None) :
            url = DEFAULT_URL
        yield scrapy.Request(url=url, callback=self.parse)
    def parseUsers(self,response):
        '''
            Function use to parse the users of a page
            
            Returns:
                list of Users
        '''
        users = [] #List of user
        user = {} # an user with a pseudo, an id and a reputation score
        for userDetail in response.css('div.user-details, .comment-user'):
            pseudo = userDetail.css('a::text').extract_first()
            if( pseudo is not None):
                userId = int(userDetail.css('a::attr(href)').extract_first().split('/')[2])
                if(userDetail.css('span.reputation-score')):
                    reputationFormat = userDetail.css('span.reputation-score::attr(title)').extract_first()\
                        .split(' ')[2]
                    if(not reputationFormat):
                        reputationFormat = userDetail.css('span.reputation-score ::text').extract_first()\
                            .replace(',','')
                else:#Comment-user
                    reputationFormat = userDetail.css('a::attr(title)').extract_first()\
                        .split(' ')[0]
                user = {
                    'pseudo' : pseudo,
                    'userId' : userId,
                    'reputation' : int(reputationFormat.replace(',',''))
                }
                
            else:  
                pseudo = userDetail.css('::text').extract_first().strip()
                if(pseudo):
                    user = {
                        'pseudo': pseudo,
                        'userId': int(pseudo[4:]),
                        'reputation': 0
                    }
            if(not user in users and user):
                users.append(user)
        return users

    def parseAnswers(self,response):
        '''
        Parse the answers of a question

        Return:
            List of answers
        ''' 
        return None

    def parseComments(self,post):
        '''
        Parse the comments of a post

        Return:
            List of comments
        ''' 
        comments = []
        comment = None;
        for comment in post.css('li'):
            comment ={
                'userId' : self.getUserId(comment.css('.comment-user')),
                'content' : comment.css('span.comment-copy ::text').extract_first(),
                'date' : comment.css('span.relativetime-clean::attr(title)').extract_first()
            }
            comments.append(comment)
        return comments

    def getUserId(self,post):
        '''
        Return the userId of a post
        Args:
            post(element) : Element with a user-details in it
        '''
        userId = None
        pseudo = post.css('a::text').extract_first()
        if(pseudo is not None):
            userId = int(post.css('a::attr(href)').extract_first().split('/')[2])                
        else:
            userId = int(post.xpath('string()').extract_first().strip()[4:])
            if(not userId):
                userId = None
        return userId

    def parse(self, response):
        '''
        Function fired when the page is download
        Args :
            response : object which travels back to the spider that issued the request.

        '''
        self.log('----Start---- ')
        page = response.url.split('/')[-2]
        questionId = int(response.css('div.question::attr(data-questionid)').extract_first())
        question = { 
            'question' : {
                'questionId': questionId,
                'title': response.css('#question-header a.question-hyperlink ::text').extract_first(),
                'favoriteCount' : int(response.css('div.favoritecount b::text').extract_first('default=0')),
                'userId' : self.getUserId(response.css('div.postcell div.owner div.user-details')),
                'content' : response.css('div.postcell div.post-text ').xpath('string()').extract_first(),
                'date': response.css('div.postcell div.owner div.user-action-time span::attr(title)').extract_first(),
                'upvoteCount': int(response.css('span.vote-count-post::text').extract_first()),
                'tags': response.css('a.post-tag ::text').extract(),
                'selectedAnswer' : int(response.css('span.vote-accepted-on').xpath('preceding-sibling::*').css('input::attr(value)').extract_first()),
                'answers' : self.parseAnswers(response),
                'comments' : self.parseComments(response.css('#comments-%s' %questionId))
                },
            'users' : self.parseUsers(response)
        }
        filename = 'question-%s.json' % page
        with open(filename, 'w') as output:
            json.dump(question,output)

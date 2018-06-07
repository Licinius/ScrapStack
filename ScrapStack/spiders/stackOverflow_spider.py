import scrapy
import json
class StackOverflowSpider(scrapy.Spider):
    '''
    Spider for stack overflow .com

    Attributes:
        name (str): Name of the spider.
    '''
    name = 'ScrapStack'
    def start_requests(self):
        '''
        First function fired with 'scrapy crawl ScrapStack'
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
    def parseUsers(self,response,users):
        '''
            Function use to parse the users of a page
            Args : 
                response(Response) : Allow to navigate throw the web page with css or/and xpath
            Returns:
                list of Users
        '''
        user = {} # an user with a pseudo, an id and a reputation score
        for userDetail in response.css('div.user-details, .comment-user').xpath('./*[not(@class="community-wiki")]/..'):
            pseudo = userDetail.css('a::text').extract_first()
            if( pseudo is not None): #The user can be real or a community wiki
                anchor = userDetail.css('a')[-1]
                pseudo = anchor.css('::text').extract_first().strip()
                userId = int(anchor.css('::attr(href)').extract_first().split('/')[2])
                if(userDetail.css('span.reputation-score')):
                    reputationFormat = userDetail.css('span.reputation-score::attr(title)').extract_first()\
                        .split(' ')[2]
                    if(not reputationFormat):
                        reputationFormat = userDetail.css('span.reputation-score ::text').extract_first(default="0")\
                            .replace(',','')
                elif(not anchor.css('[id^=history]')):#Comment-user and not community-wiki title
                    reputationFormat = anchor.css('::attr(title)').extract_first(default="0")\
                        .split(' ')[0]
                else :
                    reputationFormat = "0";
                user = {
                    'pseudo' : pseudo,
                    'userId' : userId,
                    'reputation' : int(reputationFormat.replace(',',''))
                }
                
            else:  #The user must have delete his account
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
        Args : 
            response(Response) : Allow to navigate throw the web page with css or/and xpath
            
        Return:
            List of answers
        ''' 
        answers = []
        answer = {}
        for divAnswer in response.css('div.answer'):
            answer = {
                'answerId' : int(divAnswer.css('::attr(data-answerid)').extract_first()),
                'content' : divAnswer.css('div.post-text').xpath('string()').extract_first(),
                'comments' :  self.parseComments(divAnswer.css('div.comments')),
                'upvoteCount' : int(divAnswer.css('span.vote-count-post ::text').extract_first()),
                'userId' : int(self.getUserId(self.getOwner(divAnswer))),
                'date': self.getOwner(divAnswer).xpath("..").css(".relativetime::attr(title)").extract_first(default="")
            }
            if(answer):
                answers.append(answer)
        return answers

    def parseComments(self,post):
        '''
        Parse the comments of a post
        Args : 
            post(Response) : Allow to navigate throw the web page with css or/and xpath
        Return:
            List of comments
        ''' 
        comments = []
        comment = None;
        for comment in post.css('li'):
            comment ={
                'commentId' : int(comment.css('::attr(data-comment-id)').extract_first()),
                'content' : comment.css('span.comment-copy').xpath('string()').extract_first(),
                'date' : comment.css('span.relativetime-clean::attr(title)').extract_first(),
                'upvoteCount' : int(comment.css('span.cool::text').extract_first(default=0)),
                'userId' : self.getUserId(comment.css('.comment-user'))
            }
            comments.append(comment)
        return comments

    def getUserId(self,post):
        '''
        Return the userId of a post
        Args:
            post(Response) : Element with a user-details in it
        Return: 
            userId (int) id of the user
        '''
        userId = None
        pseudo = post.css('a::text').extract_first()
        if(pseudo is not None):
            anchor = post.css('a')[-1]
            userId = int(anchor.css('::attr(href)').extract_first().split('/')[2])                
        else:
            userId = int(post.xpath('string()').extract_first().strip()[4:])
            if(not userId):
                userId = None
        return userId
    def parseRelatedQuestions(self,response):
        '''
        Function called to parse the related question of a question

        Args :
            response(Response) : object which travels back to the spider that issued the request.
        Returns:
            Links of the related questions
        '''
        relatedQuestions = []
        for link in response.css('div.related a.question-hyperlink::attr(href)').extract():
            relatedQuestions.append("https://stackoverflow.com"+link)
        return relatedQuestions

    def getOwner(self,post):
        '''
        Get the owner of a post 
        Args:
            post: Object that represent a post of stackoverflow
        Returns:
            Response : The cell of the owner, can be a anonymous owner, a community wiki or a real user
        '''
        return post.css('div.user-details')[-1]#The last div.user-details
    def parseAgain(self,response):
        '''
        Function fired if the page contains multiple page of answers
        Args :
            response(Response) : object which travels back to the spider that issued the request.
        Yields :
            A request if an other page have to be scrap
        '''
        page = response.url.split('/')[-2]
        filename = 'question-%s.json' % page
        with open(filename) as f:
            question = json.load(f) #Load data already crawled

        question['question']['answers'] = question['question']['answers'] + self.parseAnswers(response)#Add new answers
        question['users'] = self.parseUsers(response,question['users']) #Add new users
        with open(filename, 'w') as output:
            json.dump(question,output)

        nextPage = response.css('span.next').xpath('..').css('::attr(href)').extract_first()
        if nextPage is not None:
            nextPage = response.urljoin(nextPage)
            yield scrapy.Request(nextPage, callback=self.parseAgain)

    def parse(self, response):
        '''
        Function fired when the page is download
        Args :
            response(Response) : object which travels back to the spider that issued the request.

        '''
        page = response.url.split('/')[-2]
        questionId = int(response.css('div.question::attr(data-questionid)').extract_first())
        question = { 
            'question' : {
                'questionId': questionId,
                'title': response.css('#question-header a.question-hyperlink ::text').extract_first(),
                'favoriteCount' : int(response.css('div.favoritecount b::text').extract_first(default=0)),
                'userId' : self.getUserId(self.getOwner(response.css('div.question:first-child'))),
                'content' : response.css('div.postcell div.post-text ').xpath('string()').extract_first(),
                'date': response.css('div.postcell div.owner div.user-action-time span::attr(title)').extract_first(default=""),
                'upvoteCount': int(response.css('span.vote-count-post::text').extract_first()),
                'tags': response.css('a.post-tag ::text').extract(),
                'selectedAnswer' : int(response.css('div.accepted-answer::attr(data-answerid)').extract_first(default=-1)),
                'comments' : self.parseComments(response.css('#comments-%s' %questionId)),
                'answers' : self.parseAnswers(response),
                'relatedQuestions': self.parseRelatedQuestions(response)
                },
            'users' : self.parseUsers(response,[])
        }
        filename = 'question-%s.json' % page
        with open(filename, 'w') as output:
            json.dump(question,output)

        nextPage = response.css('span.next').xpath('..').css('::attr(href)').extract_first()
        if nextPage is not None:
            nextPage = response.urljoin(nextPage)
            yield scrapy.Request(nextPage, callback=self.parseAgain)
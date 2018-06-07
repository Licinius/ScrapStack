# ScrapStack!


Hi! ScrapStack allows you to download many informations on a stackoverflow page into a json file. 


# Installation

 1. Install python 2 or 3
 2. Install Twisted
 3. Install lxml
 4. Install Scrapy
	 `pip install scrapy`

## Use Scrapy
When you are in the root of the folder :

    scrapy crawl ScrapStack 
 It will launch the crawl on [this web page](https://stackoverflow.com/questions/13687346/java-hashmap-get-method-null-pointer-exception) 

If you want to execute ScrapStack with another question from stackoverflow.com 

    scrapy crawl ScrapStack -a url=<your_url>



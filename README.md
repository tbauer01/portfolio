# GIT Portfolio
## Market News Collector

Location: `./data_mining/crawl_ticker_news.py`

The market news collector consists of two main parts. The first is an RSS feed parser that uses and input CSV to
define a list of stock symbols. The feed parser will build the Google News RSS feed URL and collect the links and place
them into a data frame. The first part will also build a directory to store the data for each symbol and place the
path to the storage location into the dataframe. The second is a Scrapy web crawler that will take the list of links
and their storage locations and collect the text data for each link.

See detailed inline comments for in depth explanation

### Usage
run `python crawl_ticker_news.py -h` for complete usage

### Requirements
The necessary requirements can be installed using `pip install -r requirements.txt`

### Future Development Efforts
In the future an additional command line argument could be added which contains a list of links that have already been
crawled to prevent duplicate data.



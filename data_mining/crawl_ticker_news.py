import argparse
import feedparser
import os
import pandas as pd
import scrapy
from scrapy.crawler import CrawlerProcess
import sys
import time


'''
The spider constructor requires two arguments when being initialized by 
CrawlerProcess. The first is a list of URLs to crawl, the second is list 
where each link corresponding data should be saved. The code that builds 
the datafarme where links and output directories are stored insures these 
arguments have an equal length. If the spider is seperated from the feedparser,
care should be taken to insure the initial arguments are equal in length.
i is used to track which link is being crawled, Spider crawls until end of link
list.
'''


class RSSSpider(scrapy.spiders.Spider):
    # Identify the Spider
    name = "NewsCollect"

    def __init__(self, start_urls, output_dir, *args, **kwargs):
        super(RSSSpider, self).__init__(*args, **kwargs)
        self.start_urls = start_urls
        self.output_dir = output_dir
        self.i = 0

    '''
    The parse method is the default callback for the spider. After crawling 
    each link the parse method will create and output file where data should 
    be saved. It will then use xpath selectors to parse the css/html. The 
    parse method will attempt to extract text from the most common place it is 
    found on the website. Should that attempt fail it will try one more time 
    to extract text from the second most common place text is found. 
    '''

    def parse(self, response):
        output_filename = time.strftime("%d_%m_%Y_") + str(self.i) + ".txt"

        # Extract from the most common place for article text
        p = response.xpath('//p/text()')
        p_text = p.extract()

        # If article text was not found try the second most common place
        if not p_text:
            p_text = response.xpath('//span/text()')
            # Giving up more attempts could be nested here in the future
            if not p_text:
                print("unable to find text at link: \n"
                      + self.start_urls[self.i])
            # text was found, open a file, write link and text
            else:
                for elem in p_text:
                    file_name = self.output_dir[self.i] + output_filename
                    output_file = open(file_name, "wb")
                    data = self.start_urls[self.i] + "\n"
                    output_file.write(data.encode("utf-8"))
                    output_file.write(elem.encode("utf-8"))
                    # add extra spaces to try and prevent words from merging
                    output_file.write(" ".encode("utf-8"))
        self.i += 1
        return


'''
The method process_sym is designed to process a particular stock symbol.
Given a stock symbol and an output directory, create a symbol specific 
directory, get the RSS feed links for that symbol. Append all the information 
to the dataframe that was passed to the method. 
'''


def process_sym(stock_sym, link_df, verbose=False, output_dir='./'):
    # Create the path where ticker data will be saved
    ticker_data_dir = output_dir + "/" + stock_sym + "/"

    # Check for directory and create
    try:
        os.stat(ticker_data_dir)
    except IOError:
        os.mkdir(ticker_data_dir)

    url = 'https://news.google.com/news/rss/search/section/q/' \
          + stock_sym + '/' + stock_sym + '?hl=en&gl=US&ned=us'

    feed = feedparser.parse(url)

    if verbose:
        print(feed.entries)

    for j in range(0, len(feed.entries)):
        s = pd.Series([feed.entries[j].link, stock_sym,
                       ticker_data_dir],
                      index=['links', 'symbol', 'data_dir'])

        link_df = link_df.append(s, ignore_index=True)

        if verbose:
            print(link_df)

    return link_df


'''
argparser is used to parse command line arguments, both required and optional.
Creates the very hand --help or -h flag that helps an unfamiliar user run 
the program.
'''


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Given a stock ticker list, \
                                                  collect news articles")
    parser.add_argument('tick_config', type=str,
                        help="path to a csv file containing tickers of \
                              interest")
    parser.add_argument('-o', '--output_dir', type=str,
                        help="location to save data too, \
                              defaults to current directory")
    parser.add_argument('-v', '--verbose',  action='store_true',
                        help="add output verbosity")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="enable debug mode, saves link dataframe to CSV")
    args = parser.parse_args()
    return args


'''
The main program looks for a keyboard interrupt to terminate the program,
calls the argparser, checks for optional args and sets the output accordingly.
Creates the link storage data frame to pass to process_sym. Parse the config
argument. Note that the config input csv can contain any information as long 
as there a column titled 'symbol'. After the link dataframe is built it will 
start the crawler.
'''
try:
    # construct and parse command line arguments
    p_args = build_arg_parser()

    # create the directory where the crawler should store data for each ticker
    if p_args.output_dir is not None:
        data_dir = p_args.output_dir + "crawler_data_" \
                     + time.strftime("%d_%m_%Y_%H_%M/")
        os.mkdir(data_dir)
    else:
        data_dir = './'
    try:
        # Crate a pandas dataframe to store links, ticker, and a directory
        # where the crawler should store data
        link_storage = pd.DataFrame(columns=['links', 'symbol', 'data_dir'])

        with open(p_args.tick_config) as tickers:
            nasdaq_stocks = pd.read_csv(p_args.tick_config)
            tickers = nasdaq_stocks.Symbol
            for sym in tickers:
                link_storage = process_sym(stock_sym=sym,
                                           link_df=link_storage,
                                           output_dir=data_dir,
                                           verbose=p_args.verbose)

        if p_args.verbose:
            print(link_storage.loc[:, 'links'])

        # if debug flag is set the link dataframe is saved to a file so it
        # can be inspected
        if p_args.debug:
            link_file = data_dir + "/links.txt"
            link_storage.to_csv(link_file, header=False)

        # Create and start spider, passes the links and output directories
        # to the crawler
        process = CrawlerProcess()
        process.crawl(RSSSpider, start_urls=link_storage.loc[:, 'links'],
                      output_dir=link_storage.loc[:, 'data_dir'])
        process.start()

    except IOError:
        print('ERROR: input file does not exist')
        print(p_args.tick_config)
        sys.exit()

except KeyboardInterrupt:
    print("Received keyboard interrupt: quiting crawler")
    sys.exit()

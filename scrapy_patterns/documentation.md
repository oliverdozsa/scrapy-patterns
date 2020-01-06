## What is scrapy-patterns?
It's a library for [Scrapy](https://scrapy.org/) to help implementing spiders quicker. How? Many websites are built
around patterns. The goal of this library is to provide elements for following those patterns. All you need to do is
 tell how to extract the necessary information, and the patterns in this library will do the rest (like following links,
extracting items, etc...).

## Concepts
### Spiderlings
Spiderlings are "immature" spiders; they are not really meaningful on their own, only when combined with other 
spiderlings / spiders. They provide one functionality, like going through a list of pages from a given starting URL.
Following is a description of currently existing spiderlings.

#### Site Pager
The `scrapy_patterns.spiderlings.site_pager.SitePager` class can be used for going through a pageable part of a website.
It needs 3 user given objects to do its job:

* `scrapy_patterns.spiderlings.site_pager.NextPageUrlParser`:
  Its responsibility is to checks whether the current page has a link for the next page, and how to extract it.
  
* `scrapy_patterns.spiderlings.site_pager.ItemUrlsParser`:
  Should return the URL of items found on the page.
  
* `scrapy_patterns.spiderlings.site_pager.ItemParser`:
  Should return a Scrapy [Item](https://docs.scrapy.org/en/latest/topics/items.html#scrapy.item.Item) from the URLs
  returned by ItemUrlsParser.
 
So to use `scrapy_patterns.spiderlings.site_pager.SitePager`, you implement the above mentioned 3 interfaces, wrap it in 
`scrapy_patterns.spiderlings.site_pager.SitePageParsers`, pass it to SitePager's constructor, and then call (yield)
`scrapy_patterns.spiderlings.site_pager.SitePager.start`, which will produce a request with which the scraping will continue.
You can find an example for usage in `scrapy_patterns.spiders.category_based_spider.CategoryBasedSpider`.

#### Site Structure Discoverer
TODO
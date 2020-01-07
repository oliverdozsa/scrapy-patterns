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
`scrapy_patterns.spiderlings.site_structure_discoverer.SiteStructureDiscoverer` can read the hierarchy of a site. For example,
a site may have main categories, each of them can have sub-categories and sub-categories could have further sub-categories, 
and so on. `scrapy_patterns.spiderlings.site_structure_discoverer.SiteStructureDiscoverer` will parse this structure into a
 `scrapy_patterns.site_structure.SiteStructure` which is basically a tree, which then can be processed further.
 `scrapy_patterns.spiderlings.site_structure_discoverer.SiteStructureDiscoverer` only needs information about how to extract
the different levels of categories. This can be done through implementing a `scrapy_patterns.spiderlings.site_structure_discoverer.CategoryParser`,
for each level, and then pass a list of them to  `scrapy_patterns.spiderlings.site_structure_discoverer.SiteStructureDiscoverer`.
The last element in the list should parse the leaf categories, which won't be processed further. This means, that if the
site you want to scrape has only main categories, the list should contain one element only, if there are sub-categories, 
there should be two parsers, etc. Each parser get a response from the level above (the first element will get a starting URL
response).  
You can find an example for usage in `scrapy_patterns.spiders.category_based_spider.CategoryBasedSpider`.

### Spiders
#### Category Based Spider
Combines `scrapy_patterns.spiderlings.site_structure_discoverer.SiteStructureDiscoverer`  and 
`scrapy_patterns.spiderlings.site_pager.SitePager` to scrape sites that are based on categories, sub-categories, sub-sub-categories,
etc. and where leaf categories point to a pageable part of site from which items can be extracted.   
This spider also keeps track of its state which is saved at regular checkpoints. Upon restarting the spider, 
if progress file exists scraping will continue (from the last saved page). This progress-saving mechanism has limitations
compared to [Scrapy's pausing](https://docs.scrapy.org/en/latest/topics/jobs.html), like it won't continue exactly
where it left off, but it has the advantage that requests doesn't have to be serializable. **Because of the nature of
this mechanism, some URLs will be processed twice, resulting in possible duplicate items. You should keep this in mind
when processing them.**  
To use it inherit your spiders from it similarly how you inherit from Scrapy spiders, but also providing a starting URL, 
and rest of the needed data. You don't need to call `scrapy_patterns.spiders.category_based_spider.CategoryBasedSpider.start_requests`
as it will be handled by Scrapy. When the spider starts, it'll check whether a progress file exists, and if yes it will
continue based on it. Otherwise it starts site structure discovering.

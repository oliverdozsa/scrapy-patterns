# What is scrapy-patterns?
It's a library for [Scrapy](https://scrapy.org/) to help implementing spiders quicker. How? Many websites are built
around patterns. The goal of this library is to provide elements for following those patterns. All you need to do is
 tell how to extract the necessary information, and the patterns in this library will do the rest (like following links,
extracting items, etc...).

# Concepts
## Spiderlings
Spiderlings are "immature" spiders; they are not really meaningful on their own, only when combined with other 
spiderlings / spiders. They provide one functionality, like going through a list of pages from a given starting URL.
Following is a description of currently existing spiderlings.

### Site Pager
TODO

### Site Structure Discoverer
TODO
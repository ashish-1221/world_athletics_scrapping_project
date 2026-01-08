# import scrapy


# class AsianAthleticsSpider(scrapy.Spider):
#     name = "asian_athletics"
#     allowed_domains = ["asianathletics.com"]
#     start_urls = ["https://asianathletics.com/26th-asian-event-wise-result/"]

#     def start_requests(self):
#         # for url in self.start_urls:
#         #     req = scrapy.Request(
#         #         url = url,
#         #         callback=self.parse,
#         #         meta = {
#         #             "playwright" : True,
#         #             "playwright_include_page": True",
#         #         }
#         #     )
#         #     yield req
#         pass

#     async def parse(self, response):
#         pass
#         # page = response.meta["playwright_page"]

#         # await page.content()

#         # pass

from itertools import count
import scrapy
from datetime import datetime
import os
import logging
import logging.config


class AsianAthleticsSpider(scrapy.Spider):
    name = "asian_athletics"
    allowed_domains = ["asianathletics.com"]
    start_urls = ["https://asianathletics.com/26th-asian-event-wise-result/"]

    output_dir = "results_for_asian_athletics"

    run_id: str
    base_log_dir: str
    error_log_dir: str
    info_log_dir: str
    fail_log_dir: str

    custom_settings = {
        "ITEM_PIPELINES": {
            # "world_athletics.pipelines.WorldAthleteIndoorAnchorPipeline": 100,
            # "world_athletics.pipelines.WorldAthleteIndoorResultPipeline": 300,
        }
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)

        spider.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        spider.base_log_dir = f"logs/{spider.name}"
        spider.error_log_dir = f"{spider.base_log_dir}/error_log"
        spider.info_log_dir = f"{spider.base_log_dir}/info_log"
        spider.fail_log_dir = f"{spider.base_log_dir}/fail_log"
        os.makedirs(spider.error_log_dir, exist_ok=True)
        os.makedirs(spider.info_log_dir, exist_ok=True)
        os.makedirs(spider.fail_log_dir, exist_ok=True)

        logging.config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "standard": {
                        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                    }
                },
                "handlers": {
                    "info_file": {
                        "class": "logging.FileHandler",
                        "filename": f"{spider.info_log_dir}/info_{spider.run_id}.log",
                        "formatter": "standard",
                        "level": "INFO",
                    },
                    "error_file": {
                        "class": "logging.FileHandler",
                        "filename": f"{spider.error_log_dir}/error_{spider.run_id}.log",
                        "formatter": "standard",
                        "level": "ERROR",
                    },
                    "console": {
                        "class": "logging.StreamHandler",
                        "formatter": "standard",
                        "level": "INFO",
                    },
                },
                "root": {
                    "handlers": ["console", "info_file", "error_file"],
                    "level": "INFO",
                },
            }
        )

        spider.logger.info("Logging initialized for spider: %s", spider.name)
        return spider

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                },
                callback=self.parse,
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        html = await page.content()
        response = response.replace(body=html)

        all_result_divs = response.xpath("//div[contains(@id,'result')]")

        for div in all_result_divs:
            h5_element = div.xpath("(./h5)[1]//text()").get()

            all_rows = div.xpath(".//table//tbody//tr")
            for row in all_rows:
                pos = row.xpath("./td[1]//text()").get()
                athlete = row.xpath("./td[3]//text()").get()
                country = row.xpath("./td[4]//text()").get()
                mark = row.xpath("./td[7]//text()").get()

                yield {
                    "event_details": h5_element,
                    "position": pos,
                    "name": athlete,
                    "country": country,
                    "mark": mark,
                }

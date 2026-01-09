from socket import timeout
import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
import logging
import logging.config
import os
from datetime import datetime


class WorldAthleteIndoorSpider(scrapy.Spider):
    name = "world_athlete_indoor"
    allowed_domains = ["worldathletics.org"]
    start_urls = [
        "https://worldathletics.org/results/world-athletics-indoor-championships/2025/world-athletics-indoor-championships-7136586/men/400-metres/semi-final/summary",
        # "https://worldathletics.org/results/world-athletics-indoor-championships/2024/world-athletics-indoor-championships-7180312/women/400-metres/heats/result#resultheader",
        # "https://worldathletics.org/results/world-athletics-indoor-championships/2022/world-athletics-indoor-championships-7138985/men/400-metres/heats/result#resultheader",
    ]

    output_dir = "results_for_world_athletics_indoor_championships"

    run_id: str
    base_log_dir: str
    error_log_dir: str
    info_log_dir: str
    fail_log_dir: str

    custom_settings = {
        "ITEM_PIPELINES": {
            "world_athletics.pipelines.WorldAthleteIndoorAnchorPipeline": 100,
            "world_athletics.pipelines.WorldAthleteIndoorResultPipeline": 300,
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

    def errback_log(self, failure):
        request = failure.request
        with open(f"{self.fail_log_dir}/failed_urls_{self.run_id}.txt", "a") as f:
            f.write(request.url + "\n")

        self.logger.error(
            f"Request failed: {request.url}",
            exc_info=failure.value,
        )

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_goto_kwargs": {
                        "wait_until": "domcontentloaded",
                        "timeout": 45000,
                    },
                    "playwright_page_methods": [
                        PageMethod("wait_for_timeout", 50000),
                        PageMethod(
                            "wait_for_selector",
                            "a[data-bind*='showevents']",
                            state="visible",
                        ),
                        PageMethod("click", "a[data-bind*='showevents']"),
                    ],
                },
                callback=self.parse_anchors,
                cb_kwargs={"anchor_id": url},
            )

    async def parse_anchors(self, response, anchor_id):
        self.logger.info(f"Parsing URL: {response}")

        page = response.meta["playwright_page"]

        await page.content()

        anchors = response.xpath(
            "//div[contains(@class,'modal-dialog')]//tr[contains(@class,'eventdetailslanding')]//a"
        )
        self.logger.info(f"Found {len(anchors)} anchors on the page.")
        for anchor in anchors:
            anchor_text = anchor.xpath("normalize-space(.)").get()
            anchor_link = response.urljoin(anchor.xpath("@href").get())
            yield {
                "anchor_id": anchor_id,
                "anchor_text": anchor_text,
                "anchor_link": anchor_link,
            }

            yield response.follow(
                url=anchor_link,
                callback=self.parse_competition_rounds,
                errback=self.errback_log,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [],
                    "handle_httpstatus_list": [404],
                },
                cb_kwargs={"anchor_id": anchor_id},
            )
        await page.close()

    async def parse_competition_rounds(self, response, anchor_id):
        # self.logger.info("Inside parsing competition rounds")
        if response.status == 404:
            self.logger.warning(f"404 error for {response.url}")

        page = response.meta["playwright_page"]

        html = await page.content()

        competition_name = response.xpath(
            "normalize-space((//div[contains(@class,'col-sm-6')])[1]//h3/a/text())"
        ).get()
        competition_description_all = (
            response.xpath(
                "(//div[contains(@class,'col-sm-6') and contains(@class,'col-md-6')])[1]"
            )
            .xpath("./span/text()")
            .getall()
        )
        competition_description = " ".join(
            t.strip() for t in competition_description_all if t.strip()
        )

        # self.logger.info(competition_description)

        event_name = response.xpath(
            "normalize-space(((//div[contains(@class,'col-sm-6')])[1]//h1)[1]/text())"
        ).get()

        round_links = response.xpath(
            "//ul[contains(@class,'nav nav-tabs nav-results offset-above')]//li"
        )

        for li in round_links:
            round_name = li.xpath("normalize-space(a/text())").get()
            href = li.xpath("a/@href").get()
            if not href:
                continue
            url = response.urljoin(href)
            yield response.follow(
                url=url,
                callback=self.parse_rounds,
                errback=self.errback_log,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "handle_httpstatus_list": [404],
                },
                cb_kwargs={
                    "competition_name": competition_name,
                    "competition_description": competition_description,
                    "event_name": event_name,
                    "round_name": round_name,
                    "anchor_id": anchor_id,
                },
            )
        await page.close()

    async def parse_rounds(
        self,
        response,
        round_name,
        competition_name,
        event_name,
        anchor_id,
        competition_description,
    ):
        if response.status == 404:
            self.logger.warning(f"404 error for {response.url}")
        page = response.meta["playwright_page"]

        await page.content()
        if round_name.lower().strip() != "final":
            await page.wait_for_load_state("networkidle")
            nav = page.locator("div.res-nav-container")

            summary_li = nav.locator("li", has_text="Summary")

            if await summary_li.count() == 0:
                self.logger.warning("Summary tab not found on %s", response.url)
                return

            is_active = await summary_li.evaluate(
                "el => el.classList.contains('active')"
            )

            if not is_active:
                await summary_li.locator("a").click()

            await page.wait_for_selector(
                "div#results.site-container div.row table.records-table", timeout=15000
            )

            html = await page.content()

            response = response.replace(body=html)

            rows = response.xpath(
                ".//table[contains(@class,'records-table')]/tbody//tr"
            )

            for row in rows:
                pos = row.xpath('./td[@data-th="POS"]/text()').get()
                rank = row.css("td[data-th='Rank']::text").get()
                heat = row.css("td[data-th='Heat']::text").get()
                athlete_name = row.xpath(
                    "normalize-space(string(.//td[translate(@data-th,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='athlete']//a))"
                ).get()
                # athlete_name = " ".join(t.strip() for t in athlete_name if t.strip())
                country = row.xpath('./td[@data-th="COUNTRY"]//text()').getall()
                mark = " ".join(
                    t.strip()
                    for t in row.css("td[data-th='RESULTS'] span::text").getall()
                    if t.strip()
                )
                yield {
                    "anchor_id": anchor_id,
                    "competition_name": competition_name,
                    "competition_description": competition_description,
                    "event_name": event_name,
                    "round_name": round_name,
                    "position": pos,
                    "rank": rank,
                    "heat": heat,
                    "athlete": athlete_name,
                    "country": country,
                    "mark": mark,
                }
        else:
            await page.wait_for_load_state("networkidle")
            nav = page.locator("div.res-nav-container.module")

            summary_li = nav.locator("li", has_text="Result")

            if await summary_li.count() == 0:
                self.logger.warning("Final tab not found on %s", response.url)
                return

            is_active = await summary_li.evaluate(
                "el => el.classList.contains('active')"
            )

            if not is_active:
                await summary_li.locator("a").click()

            await page.wait_for_selector(
                "div#results.site-container div.row table.records-table", timeout=15000
            )

            html = await page.content()

            response = response.replace(body=html)
            rows = response.xpath(
                "//table[contains(@class,'records-table') and contains(@class,'clickable')]/tbody/tr"
            )

            for row in rows:
                pos = row.xpath('./td[@data-th="POS"]/text()').get()
                rank = row.css("td[data-th='Rank']::text").get()
                heat = row.css("td[data-th='Heat']::text").get()
                athlete_name = row.xpath(
                    "normalize-space(string(.//td[translate(@data-th,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='athlete']//a))"
                ).get()

                # athlete_name = " ".join(t.strip() for t in athlete_name if t.strip())
                country = row.xpath('./td[@data-th="COUNTRY"]//text()').getall()
                mark = " ".join(
                    t.strip()
                    for t in row.css("td[data-th='RESULTS'] span::text").getall()
                    if t.strip()
                )

                if not mark:
                    mark = " ".join(
                        t.strip()
                        for t in row.css("td[data-th='MARK'] ::text").getall()
                        if t.strip()
                    )

                yield {
                    "anchor_id": anchor_id,
                    "competition_name": competition_name,
                    "competition_description": competition_description,
                    "event_name": event_name,
                    "round_name": round_name,
                    "position": pos,
                    "rank": rank,
                    "heat": heat,
                    "athlete": athlete_name,
                    "country": country,
                    "mark": mark,
                }

import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime


class WorldAthleteIndoorSpider(scrapy.Spider):
    name = "world_athlete_indoor"
    allowed_domains = ["worldathletics.org"]
    start_urls = [
        "https://worldathletics.org/results/world-athletics-indoor-championships/2025/world-athletics-indoor-championships-7136586/men/400-metres/semi-final/summary",
        "https://worldathletics.org/results/world-athletics-indoor-championships/2024/world-athletics-indoor-championships-7180312/women/400-metres/heats/result#resultheader",
        "https://worldathletics.org/results/world-athletics-indoor-championships/2022/world-athletics-indoor-championships-7138985/men/400-metres/heats/result#resultheader",
    ]

    output_dir = "results_for_world_athletics_indoor_championships"

    # log_dir = "logs"
    # run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    custom_settings = {
        "ITEM_PIPELINES": {
            "world_athletics.pipelines.WorldAthleteIndoorAnchorPipeline": 100,
        },
        # "LOG_ENABLED": True,
        # "LOG_LEVEL": "DEBUG",
        # "LOG_FILE": f"logs/{name}/world_athlete_indoor_{run_id}.log",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_timeout", 100000),
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

        # yield response.follow(
        #     url=anchor_link,
        #     callback=self.parse_competition_rounds,
        #     meta={
        #         "playwright": True,
        #         "playwright_include_page": True,
        #         "playwright_page_methods": [],
        #         "handle_httpstatus_list": [404],
        #     },
        # )

    def parse_modal(self, response, anchor_id):
        """
        Extract all event links from the modal
        """

        event_links = response.xpath(
            "//div[contains(@class,'modal-dialog')]"
            "//tr[contains(@class,'eventdetailslanding')]//a/@href"
        ).getall()

        self.logger.info(f"Found {len(event_links)} event links")

        for href in event_links:
            url = response.urljoin(href)

            # FOLLOW WITH PURE SCRAPY
            # yield scrapy.Request(
            #     url=url,
            #     callback=self.parse_event_results,
            #     meta={
            #         "playwright": False,  # EXPLICIT
            #     },
            #     cb_kwargs={
            #         "anchor_id": anchor_id,
            #     },
            # )

    async def parse_competition_rounds(self, response):
        self.logger.info("Inside parsing competition rounds")
        if response.status == 404:
            self.logger.warning(f"404 error for {response.url}")

        page = response.meta["playwright_page"]

        html = await page.content()

        competition_name = response.xpath(
            '//div[@class = "col-sm-6 col-md-6"]/h3/a/text()'
        ).get()
        competition_description = response.xpath(
            '/span[@class = "_label date"]/text()'
        ).get()
        event_name = response.xpath(
            'normalize-space(//div[@class = "col-sm-6 col-md-6"]/h1/text())'
        ).get()
        round_name_list = response.xpath(
            '//ul[@class = "nav nav-tabs nav-results offset-above"]//li/a/text()'
        ).get()
        self.logger.info(
            f"Scrapping {competition_name} for {event_name} with rounds {round_name_list} "
        )
        for li in response.xpath(
            "//ul[@class = 'nav nav-tabs nav-results offset-above']//li"
        ):
            round_name = li.xpath("normalize-space(a/text())").get()
            href = li.xpath("a/@href").get()
            if not href:
                continue
            url = response.urljoin(href)
            # print(round_name, "<-------round name")
            # print(url, "<---------- url")
            # print("\n\n")

            # yield response.follow(
            #     url,
            #     callback=self.parse_rounds,
            #     cb_kwargs={
            #         "round_name": round_name,
            #         "competition_name": competition_name,
            #         "competition_description": competition_description,
            #         # "event_name": event_name,
            #         "round_name_list": round_name_list,
            #     },
            # )
        await page.close()

    def parse_rounds(
        self,
        response,
        round_name,
        competition_name,
        competition_description,
        round_name_list,
    ):
        self.logger.info("Parsing the rounds")
        # event_name = response.xpath(
        #     "normalize-space(//div[@class = 'col-sm-6 col-md-6']/h1/text())"
        # ).get()

        # self.logger.info(
        #     f"Scrapping for {competition_name} {round_name} containing {round_name_list} for event {event_name}"
        # )

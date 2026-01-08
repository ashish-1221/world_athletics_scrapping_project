import scrapy
from scrapy_playwright.page import PageMethod


class WorldAthleteIndoorSpider(scrapy.Spider):
    name = "world_athlete_indoor"
    allowed_domains = ["worldathletics.org"]
    start_urls = [
        "https://worldathletics.org/results/world-athletics-indoor-championships/2025/world-athletics-indoor-championships-7136586/men/400-metres/semi-final/summary"
    ]

    output_dir = "results_for_world_athletics_indoor_championships"

    custom_settings = {
        "ITEM_PIPELINES": {
            "world_athletics.pipelines.AnchorGroupingPipeline": 300,
        }
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_timeout", 10000),
                        PageMethod(
                            "wait_for_selector",
                            "a[data-bind*='showevents']",
                            state="visible",
                        ),
                        PageMethod("click", "a[data-bind*='showevents']"),
                    ],
                },
                callback=self.parse,
                cb_kwargs={"anchor_id": url},
            )

    async def parse_anchors(self, response, anchor_id):
        self.logger.info(f"Parsing URL: {response}")
        anchors = response.xpath("//tr//a")
        self.logger.info(f"Found {len(anchors)} anchors on the page.")
        for anchor in anchors:
            anchor_text = anchor.xpath("normalize-space(.)").get()
            anchor_link = response.urljoin(anchor.xpath("@href").get())
            yield {
                "anchor_id": anchor_id,
                "anchor_text": anchor_text,
                "anchor_link": anchor_link,
            }

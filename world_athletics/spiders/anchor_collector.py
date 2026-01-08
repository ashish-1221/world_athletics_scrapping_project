from datetime import datetime
import scrapy


class AnchorCollectorSpider(scrapy.Spider):
    name = "anchor-collector"
    allowed_domains = ["worldathletics.org"]
    start_urls = [
        "https://worldathletics.org/competitions/world-athletics-championships/world-athletics-championships-budapest-2023-7138987/timetable/bydiscipline",
    ]

    output_dir = "results_for_world_athletics_championships"

    log_dir = "logs"
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # def parse(self, response):
    #     pass

    custom_settings = {
        "ITEM_PIPELINES": {
            "world_athletics.pipelines.AnchorGroupingPipeline": 300,
        },
        "LOG_ENABLED": True,
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE": f"logs/{name}/world_athlete_{run_id}.log",
    }

    def start_requests(self):
        # GET request
        for url in self.start_urls:
            self.championship_name = url.split("/")[-3]
            req = scrapy.Request(
                url=url,
                callback=self.parse,
                meta={"playwright": True, "playwright_include_page": True},
            )
            yield req

    async def parse(self, response, **kwargs):
        page = response.meta["playwright_page"]
        await page.content()
        ## Get list of all anchors
        all_anchors_list = response.xpath("//body//table//tr//a")

        seen = set()
        # open("anchors_list.txt", "w", encoding="utf-8").write(all_anchors_list)
        # print(all_anchors_list)
        ## Iterate through the anchors
        for anchor in all_anchors_list:
            href = anchor.xpath("@href").get()

            if not href:
                continue

            anchor_url = response.urljoin(href)

            if anchor_url in seen:
                continue

            seen.add(anchor_url)
            # open("anchors_list.txt", "a", encoding="utf-8").write(anchor_url)
            # print(anchor_url)
            yield response.follow(
                url=anchor_url,
                callback=self.parse_round,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "handle_httpstatus_list": [404],
                },
                cb_kwargs={"anchor_id": anchor_url},
            )
        await page.close()

    async def parse_round(self, response, anchor_id):
        """
        Docstring for parse_round
        Prepare event_name,round_name along with result url

        :param self: Description
        :param response: Description
        """
        if response.status == 404:
            self.logger.warning(f"404 error for {response.url}")
        page = response.meta["playwright_page"]

        html = await page.content()
        # print("Writing to the file")
        # open("rendered.html", "w", encoding="utf-8").write(html)

        event_name = (
            response.css('[data-name="timetable-day-title"]').xpath("h1/text()").get()
        )
        self.logger.info(f"Event Name :- {event_name}")
        # self.event_name = event_name

        if event_name is not None:
            rows_list = response.css('[data-name="timetable-body"]').xpath("//tr")
            # self.logger.info(f"{rows_list}")
            # open("round_list.txt", "a", encoding="utf-8").write(rows_list)

            ## Iterate through responses of rows_list
            for round_response in rows_list[1:]:
                round_name = round_response.xpath("./td[1]/span/text()").get()
                # self.round_name = round_name
                href = round_response.xpath("./td[6]/a/@href").get()
                # self.logger.info(href)
                round_url_href = response.urljoin(href)

                self.logger.info(f"Round Name :- {round_name}")
                # self.logger.info(f"Round URL :- {round_url_href}")

                yield response.follow(
                    url=round_url_href,
                    callback=self.parse_tabs,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "handle_httpstatus_list": [404],
                    },
                    cb_kwargs={
                        "event_name": event_name,
                        "round_name": round_name,
                        "anchor_id": anchor_id,
                    },
                )
        await page.close()

    async def parse_tabs(self, response, event_name, round_name, anchor_id):
        if response.status == 404:
            self.logger.warning(f"404 error for {response.url}")

        page = response.meta["playwright_page"]

        html = await page.content()

        round_sections = response.xpath("(//section)[1]//ul//li")
        for round in round_sections:
            result_name = round.xpath("./a//text()").get()
            href = round.xpath("./a/@href").get()
            result_href = response.urljoin(href)
            # self.result_name = result_name

            self.logger.info(f"Extracting for Result name :- {result_name}")
            # self.logger.info(f"Result URL : {result_href}")

            yield response.follow(
                url=result_href,
                callback=self.parse_results,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "handle_httpstatus_list": [404],
                },
                cb_kwargs={
                    "event_name": event_name,
                    "round_name": round_name,
                    "result_name": result_name,
                    "anchor_id": anchor_id,
                },
            )
        await page.close()

    async def parse_results(
        self, response, result_name, event_name, round_name, anchor_id
    ):
        if response.status == 404:
            self.logger.warning(f"404 error for {response.url}")

        page = response.meta["playwright_page"]

        html = await page.content()

        if result_name.lower().strip() != "final":
            self.logger.info(f"Clicking on the Summary Section for {result_name}")
            await page.click("div[role='button']:has-text('Summary')")
            await page.wait_for_selector(
                "div[role='button']:has-text('Summary').ResultsLOC_unitTabActive__1e8HU"
            )
            html = await page.content()
            sel = scrapy.Selector(text=html)
            rows = sel.xpath('//table[contains(@class,"Table_table__2zsdR")]//tr')

            # self.logger.info(f"Rows Section :- {rows}")

            for row in rows:
                position = row.xpath("./td[1]//text()").get()
                rank = row.xpath("./td[2]//text()").get()
                heat = row.xpath("./td[3]//text()").get()
                bib = row.xpath("./td[4]//text()").get()
                country = row.xpath("./td[5]//text()").get()
                athlete = row.xpath("./td[6]//text()").get()
                mark = row.xpath("./td[7]//text()").get()
                details = row.xpath("./td[8]//text()").get()
                reaction_time = row.xpath("./td[9]//text()").get()
                wind = row.xpath("./td[10]//text()").get()

                yield {
                    "anchor_id": anchor_id,
                    "championship": self.championship_name,
                    "event_name": event_name,
                    "round_name": round_name,
                    "result_name": result_name,
                    "position": position,
                    "rank": rank,
                    "heat": heat,
                    "bib": bib,
                    "country": country,
                    "athlete": athlete,
                    "mark": mark,
                    "details": details,
                    "reaction_time": reaction_time,
                    "wind": wind,
                }

        if result_name.lower().strip() == "final":
            self.logger.info(f"Clicking on the Final Section for {result_name}")
            await page.click("div[role='button']:has-text('Final')")
            await page.wait_for_selector(
                "div[role='button']:has-text('Final').ResultsLOC_unitTabActive__1e8HU"
            )
            html = await page.content()
            sel = scrapy.Selector(text=html)
            rows = sel.xpath('//table[contains(@class,"Table_table__2zsdR")]//tr')

            # self.logger.info(f"Rows Section :- {rows}")

            for row in rows:
                position = row.xpath("./td[1]//text()").get()
                # rank = row.xpath("./td[2]//text()").get()
                # heat = row.xpath("./td[3]//text()").get()
                bib = row.xpath("./td[2]//text()").get()
                country = row.xpath("./td[3]//text()").get()
                athlete = row.xpath("./td[4]//text()").get()
                mark = row.xpath("./td[5]//text()").get()
                # details = row.xpath("./td[8]//text()").get()
                reaction_time = row.xpath("./td[6]//text()").get()
                # wind = row.xpath("./td[10]//text()").get()

                yield {
                    "anchor_id": anchor_id,
                    "championship": self.championship_name,
                    "event_name": event_name,
                    "round_name": round_name,
                    "result_name": result_name,
                    "position": position,
                    "rank": "",
                    "heat": "",
                    "bib": bib,
                    "country": country,
                    "athlete": athlete,
                    "mark": mark,
                    "details": "",
                    "reaction_time": reaction_time,
                    "wind": "",
                }
        await page.close()

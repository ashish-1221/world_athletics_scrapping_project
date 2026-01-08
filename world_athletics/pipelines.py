# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


# class WorldAthleticsPipeline:
#     def process_item(self, item, spider):
#         return item


from collections import defaultdict
import json
import os


class AnchorGroupingPipeline:

    def open_spider(self, spider):
        self.output_dir = getattr(spider, "output_dir", "results")
        self.data = defaultdict(list)
        os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        event_name = item.get("event_name", "unknown_event")
        self.data[event_name].append(dict(item))
        return item

    def close_spider(self, spider):
        for event_name, records in self.data.items():
            safe_name = event_name.replace(" ", "_").lower()
            path = os.path.join(self.output_dir, f"{safe_name}.json")

            with open(path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)


class WorldAthleteIndoorAnchorPipeline:
    def open_spider(self, spider):
        self.output_dir = getattr(spider, "output_dir", "results")
        self.data = defaultdict(list)
        os.makedirs(self.output_dir, exist_ok=True)

        ## Createa file path to store anchors
        self.file_path = os.path.join(self.output_dir, "anchors.json")
        self.file = open(self.file_path, "w", encoding="utf-8")

        self.items = []

    def process_item(self, item, spider):
        if "anchor_link" not in item:
            return item

        self.items.append(dict(item))
        return item

    def close_spider(self, spider):
        json.dump(self.items, self.file, ensure_ascii=False, indent=2)
        self.file.close()

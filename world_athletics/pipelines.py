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
        anchor_id = item["anchor_id"]
        self.data[anchor_id].append(dict(item))
        return item

    def close_spider(self, spider):
        for anchor_id, records in self.data.items():
            safe_name = anchor_id.split("/")[-1]
            path = os.path.join(self.output_dir, f"{safe_name}.json")

            with open(path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)


class WorldAthleteIndoorPipeline:
    def open_spider(self, spider):
        self.output_dir = getattr(spider, "output_dir", "results")
        self.data = defaultdict(list)
        os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        self.item.append()

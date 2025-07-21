import os
import json
import asyncio
from datetime import datetime
from scraping.scraper import Scraper
from common.data import DataEntity, DataSource
import twikit_scraper  # ваш модуль

class TwikitProvider(Scraper):
    def __init__(self, config, session):
        super().__init__(config, session)
        # config — это тот, что из scraping_config.json
        self.cookies_file = config["cookies_path"]
        labels_cfg = config.get("labels_to_scrape", [])
        # Предполагаем, одна группа labels_to_scrape
        self.search_keywords = labels_cfg[0]["label_choices"] if labels_cfg else []
        self.tweets_per_keyword = labels_cfg[0]["max_data_entities"] if labels_cfg else 100

    def _write_temp_config(self):
        # Записываем файл config.json для twikit_scraper
        cfg = {
            "cookies_file": self.cookies_file,
            "search_keywords": self.search_keywords,
            "tweets_per_keyword": self.tweets_per_keyword
        }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)

    def scrape(self):
        # Подготовим config.json
        self._write_temp_config()
        # Запустим асинхронную функцию twikit_scraper.scrape_twitter()
        items = asyncio.run(twikit_scraper.scrape_twitter())
        entities = []
        for i in items:
            # полей tweet: uri, datetime, source, label={"name":term}, content, content_size_bytes
            entities.append(DataEntity(
                uri=i["uri"],
                datetime=i["datetime"],
                source=DataSource.TWITTER,
                label=i["label"]["name"],
                content=i["content"],
                content_size_bytes=i["content_size_bytes"]
            ))
        return entities

    def validate(self):
        return super().validate()

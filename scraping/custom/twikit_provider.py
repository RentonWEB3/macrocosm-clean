import os
import json
import asyncio
from scraping.scraper import Scraper, ScrapeConfig
from common.data import DataEntity, DataSource, DataLabel
import twikit_scraper  # ваш модуль

class TwikitProvider(Scraper):
    """Simple scraper provider that wraps the ``twikit_scraper`` module."""

    def __init__(self, *_args, **_kwargs):
        # cookies path can be overridden via environment variable
        self.cookies_file = os.getenv("TWIKIT_COOKIES_FILE", "twitter_cookies.json")
        self.search_keywords = []
        self.tweets_per_keyword = 100
        self.session = _kwargs.get("session")

    def _write_temp_config(self):
        # Записываем файл config.json для twikit_scraper
        cfg = {
            "cookies_file": self.cookies_file,
            "search_keywords": self.search_keywords,
            "tweets_per_keyword": self.tweets_per_keyword
        }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)

    async def scrape(self, scrape_config: ScrapeConfig) -> list[DataEntity]:
        """Run the twikit scraper and convert results to ``DataEntity``."""

        # Update search keywords and tweet limits from the scrape config
        if scrape_config.labels:
            self.search_keywords = [label.value for label in scrape_config.labels]
        if scrape_config.entity_limit:
            self.tweets_per_keyword = scrape_config.entity_limit

        self._write_temp_config()
        items = await twikit_scraper.scrape_twitter()

        entities: list[DataEntity] = []
        for item in items:
            entities.append(
                DataEntity(
                    uri=item["uri"],
                    datetime=item["datetime"],
                    source=DataSource.X,
                    label=DataLabel(value=item["label"]["name"]),
                    content=item["content"].encode("utf-8")
                    if isinstance(item["content"], str)
                    else item["content"],
                    content_size_bytes=item["content_size_bytes"],
                )
            )
        return entities

    async def validate(self, entities):
        """Twikit scraper currently has no validation step."""
        return []

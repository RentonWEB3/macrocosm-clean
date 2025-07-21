import json
import asyncio
from scraping.scraper import Scraper, ValidationResult, HFValidationResult
from common.data import DataEntity, DataLabel, DataSource
import twikit_scraper  # ваш модуль
from datetime import datetime

class TwikitProvider(Scraper):
    def __init__(self, config=None, session=None):
        self.session = session
        scraper_key = "X.microworlds"   # без импортов

        # Если передали CoordinatorConfig (есть поле scraper_configs)
        if hasattr(config, "scraper_configs"):
            scraper_cfg = config.scraper_configs.get(scraper_key)
        else:
            scraper_cfg = config  # возможно уже ScraperConfig

        if scraper_cfg is None:
            print("WARN: scraper_cfg for X.microworlds not found")
            self.search_keywords = []
            self.tweets_per_keyword = 100
            self.cookies_file = "twitter_cookies.json"
        else:
            labels_cfg = getattr(scraper_cfg, "labels_to_scrape", [])
            if labels_cfg:
                first = labels_cfg[0]
                self.search_keywords = [lbl.value for lbl in getattr(first, "label_choices", [])]
                self.tweets_per_keyword = getattr(first, "max_data_entities", 100)
            else:
                self.search_keywords = []
                self.tweets_per_keyword = 100
            self.cookies_file = "twitter_cookies.json"

        print("DEBUG Twikit search_keywords:", self.search_keywords, "tweets_per_keyword:", self.tweets_per_keyword, "cookies_file:", self.cookies_file)

    def _write_temp_config(self):
        # Записываем файл config.json для twikit_scraper
        cfg = {
            "cookies_file": self.cookies_file,
            "search_keywords": self.search_keywords,
            "tweets_per_keyword": self.tweets_per_keyword
        }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)

    async def scrape(self, scrape_config=None):
        """Scrapes twitter using the ``twikit`` helper module."""

        # Подготовим config.json
        self._write_temp_config()

        # Запустим асинхронную функцию twikit_scraper.scrape_twitter()
        items = await twikit_scraper.scrape_twitter()
        entities = []
        for i in items:
            raw_dt = i["datetime"]
            try:
                dt_obj = datetime.strptime(raw_dt, "%a %b %d %H:%M:%S %z %Y")
            except Exception as e:
                print("DEBUG cannot parse datetime:", raw_dt, e)
                continue  # пропускаем проблемный элемент

            content_bytes = i["content"].encode("utf-8")
            entities.append(
                DataEntity(
                    uri=i["uri"],
                    datetime=dt_obj,  # ВАЖНО: dt_obj, НЕ raw_dt
                    source=DataSource.X,
                    label=DataLabel(value=i["label"]["name"]),
                    content=content_bytes,
                    content_size_bytes=len(content_bytes),
                )
            )
        return entities

    async def validate(self, entities):
        """Perform a very basic validation of scraped entities."""

        if not entities:
            return []

        results = []
        for entity in entities:
            is_valid = bool(getattr(entity, "content", "").strip())
            results.append(
                ValidationResult(
                    is_valid=is_valid,
                    content_size_bytes_validated=len(entity.content.encode("utf-8")) if entity.content else 0,
                    reason="" if is_valid else "Empty content",
                )
            )

        return results

    async def validate_hf(self, entities) -> HFValidationResult:
        """Validate HF dataset entries.

        This basic implementation simply marks all provided entities as valid
        without performing any external checks. It returns an
        ``HFValidationResult`` mirroring the structure used by other scrapers so
        that the class satisfies :class:`Scraper`'s abstract interface.

        Args:
            entities: An iterable of HF dataset rows represented as dictionaries.

        Returns:
            HFValidationResult indicating success for all rows.
        """

        if not entities:
            return HFValidationResult(
                is_valid=True,
                validation_percentage=100.0,
                reason="No entities to validate",
            )

        results = [
            ValidationResult(
                is_valid=True,
                content_size_bytes_validated=0,
                reason="",
            )
            for _ in entities
        ]

        valid_count = len([r for r in results if r.is_valid])
        validation_percentage = (valid_count / len(results)) * 100

        return HFValidationResult(
            is_valid=True,
            validation_percentage=validation_percentage,
            reason=f"Validation Percentage = {validation_percentage}",
        )


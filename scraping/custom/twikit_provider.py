import json
import asyncio
from scraping.scraper import Scraper, ValidationResult, HFValidationResult
from common.data import DataEntity, DataSource
import twikit_scraper  # ваш модуль

class TwikitProvider(Scraper):
    def __init__(self, config, session):
        self.session = session
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

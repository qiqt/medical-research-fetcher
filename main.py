from datetime import datetime
import asyncio
import logging
from pathlib import Path
import sys

from lib import (
    load_config,
    LocalStorage,
    PubMedClient,
    ArticleProcessor,
)

sys.path.append(str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    try:
        config = load_config()

        storage = LocalStorage(base_path=config.storage_path)
        client = PubMedClient(config.get_pubmed_config())
        processor = ArticleProcessor(client, storage)

        queries = [
            ("pancreatic cancer immunotherapy 2023", 5),
        ]

        for query, max_results in queries:
            logger.info(f"\nProcessing query: {query}")
            summary = await processor.search_and_process(query, max_results)

            logger.info(f"\nQuery processing complete:")
            logger.info(f"Query: {query}")
            logger.info(f"Articles found: {summary['total_articles_found']}")
            logger.info(f"Successfully processed: {
                        summary['successfully_processed']}")
            logger.info(f"Failed: {summary['failed_processing']}")

            if summary.get('failed_pmids'):
                logger.info(f"Failed PMIDs: {
                            ', '.join(summary['failed_pmids'])}")

            logger.info("-" * 50)

    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

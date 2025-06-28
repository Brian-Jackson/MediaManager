import logging
from abc import ABC, abstractmethod

import media_manager.config
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.tv.schemas import Show
from media_manager.movies.schemas import Movie

log = logging.getLogger(__name__)


class AbstractMetadataProvider(ABC):
    storage_path = media_manager.config.BasicConfig().image_directory

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def get_show_metadata(self, id: int = None) -> Show:
        raise NotImplementedError()

    @abstractmethod
    def get_movie_metadata(self, id: int = None) -> Movie:
        raise NotImplementedError()

    @abstractmethod
    def search_show(
        self, query: str | None = None
    ) -> list[MetaDataProviderSearchResult]:
        raise NotImplementedError()

    @abstractmethod
    def search_movie(
        self, query: str | None = None
    ) -> list[MetaDataProviderSearchResult]:
        raise NotImplementedError()

    @abstractmethod
    def download_show_poster_image(self, show: Show) -> bool:
        """
        Downloads the poster image for a show.
        :param show: The show to download the poster image for.
        :return: True if the image was downloaded successfully, False otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    def download_movie_poster_image(self, movie: Movie) -> bool:
        """
        Downloads the poster image for a show.
        :param movie: The show to download the poster image for.
        :return: True if the image was downloaded successfully, False otherwise.
        """
        raise NotImplementedError()




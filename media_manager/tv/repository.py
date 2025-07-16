from sqlalchemy import select, delete
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)  # Keep SQLAlchemyError for broader exception handling
from sqlalchemy.orm import Session, joinedload

from media_manager.torrent.models import Torrent
from media_manager.torrent.schemas import TorrentId, Torrent as TorrentSchema
from media_manager.tv import log
from media_manager.tv.models import Season, Show, Episode, SeasonRequest, SeasonFile
from media_manager.exceptions import NotFoundError
from media_manager.tv.schemas import (
    Season as SeasonSchema,
    SeasonId,
    Show as ShowSchema,
    ShowId,
    Episode as EpisodeSchema,  # Added EpisodeSchema import
    SeasonRequest as SeasonRequestSchema,
    SeasonFile as SeasonFileSchema,
    SeasonNumber,
    SeasonRequestId,
    RichSeasonRequest as RichSeasonRequestSchema,
    EpisodeId,
)


class TvRepository:
    """
    Repository for managing TV shows, seasons, and episodes in the database.
    Provides methods to retrieve, save, and delete shows and seasons.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_show_by_id(self, show_id: ShowId) -> ShowSchema:
        """
        Retrieve a show by its ID, including seasons and episodes.

        :param show_id: The ID of the show to retrieve.
        :return: A Show object if found.
        :raises NotFoundError: If the show with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to retrieve show with id: {show_id}")
        try:
            stmt = (
                select(Show)
                .where(Show.id == show_id)
                .options(joinedload(Show.seasons).joinedload(Season.episodes))
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                log.warning(f"Show with id {show_id} not found.")
                raise NotFoundError(f"Show with id {show_id} not found.")
            log.info(f"Successfully retrieved show with id: {show_id}")
            return ShowSchema.model_validate(result)
        except SQLAlchemyError as e:
            log.error(f"Database error while retrieving show {show_id}: {e}")
            raise

    def get_show_by_external_id(
        self, external_id: int, metadata_provider: str
    ) -> ShowSchema:
        """
        Retrieve a show by its external ID, including nested seasons and episodes.

        :param external_id: The ID of the show to retrieve.
        :param metadata_provider: The metadata provider associated with the ID.
        :return: A Show object if found.
        :raises NotFoundError: If the show with the given external ID and provider is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(
            f"Attempting to retrieve show with external_id: {external_id} and provider: {metadata_provider}"
        )
        try:
            stmt = (
                select(Show)
                .where(Show.external_id == external_id)
                .where(Show.metadata_provider == metadata_provider)
                .options(joinedload(Show.seasons).joinedload(Season.episodes))
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                log.warning(
                    f"Show with external_id {external_id} and provider {metadata_provider} not found."
                )
                raise NotFoundError(
                    f"Show with external_id {external_id} and provider {metadata_provider} not found."
                )
            log.info(
                f"Successfully retrieved show with external_id: {external_id} and provider: {metadata_provider}"
            )
            return ShowSchema.model_validate(result)
        except SQLAlchemyError as e:
            log.error(
                f"Database error while retrieving show by external_id {external_id}: {e}"
            )
            raise

    def get_shows(self) -> list[ShowSchema]:
        """
        Retrieve all shows from the database.

        :return: A list of Show objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug("Attempting to retrieve all shows.")
        try:
            stmt = select(Show).options(
                joinedload(Show.seasons).joinedload(Season.episodes)
            )  # Eager load seasons and episodes
            results = self.db.execute(stmt).scalars().unique().all()
            log.info(f"Successfully retrieved {len(results)} shows.")
            return [ShowSchema.model_validate(show) for show in results]
        except SQLAlchemyError as e:
            log.error(f"Database error while retrieving all shows: {e}")
            raise

    def save_show(self, show: ShowSchema) -> ShowSchema:
        """
        Save a new show or update an existing one in the database.

        :param show: The Show object to save.
        :return: The saved Show object.
        :raises ValueError: If a show with the same primary key already exists (on insert).
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to save show: {show.name} (ID: {show.id})")
        db_show = self.db.get(Show, show.id) if show.id else None

        if db_show:  # Update existing show
            log.debug(f"Updating existing show with ID: {show.id}")
            db_show.external_id = show.external_id
            db_show.metadata_provider = show.metadata_provider
            db_show.name = show.name
            db_show.overview = show.overview
            db_show.year = show.year
        else:  # Insert new show
            log.debug(f"Creating new show: {show.name}")
            db_show = Show(
                id=show.id,
                external_id=show.external_id,
                metadata_provider=show.metadata_provider,
                name=show.name,
                overview=show.overview,
                year=show.year,
                ended=show.ended,
                seasons=[
                    Season(
                        id=season.id,
                        show_id=show.id,
                        number=season.number,
                        external_id=season.external_id,
                        name=season.name,
                        overview=season.overview,
                        episodes=[
                            Episode(
                                id=episode.id,
                                season_id=season.id,
                                number=episode.number,
                                external_id=episode.external_id,
                                title=episode.title,
                            )
                            for episode in season.episodes
                        ],
                    )
                    for season in show.seasons
                ],
            )
            self.db.add(db_show)

        try:
            self.db.commit()
            self.db.refresh(db_show)
            log.info(f"Successfully saved show: {db_show.name} (ID: {db_show.id})")
            return ShowSchema.model_validate(db_show)
        except IntegrityError as e:
            self.db.rollback()
            log.error(f"Integrity error while saving show {show.name}: {e}")
            raise ValueError(
                f"Show with this primary key or unique constraint violation: {e.orig}"
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(f"Database error while saving show {show.name}: {e}")
            raise

    def delete_show(self, show_id: ShowId) -> None:
        """
        Delete a show by its ID.

        :param show_id: The ID of the show to delete.
        :raises NotFoundError: If the show with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to delete show with id: {show_id}")
        try:
            show = self.db.get(Show, show_id)
            if not show:
                log.warning(f"Show with id {show_id} not found for deletion.")
                raise NotFoundError(f"Show with id {show_id} not found.")
            self.db.delete(show)
            self.db.commit()
            log.info(f"Successfully deleted show with id: {show_id}")
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(f"Database error while deleting show {show_id}: {e}")
            raise

    def get_season(self, season_id: SeasonId) -> SeasonSchema:
        """
        Retrieve a season by its ID.

        :param season_id: The ID of the season to get.
        :return: A Season object.
        :raises NotFoundError: If the season with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to retrieve season with id: {season_id}")
        try:
            season = self.db.get(Season, season_id)
            if not season:
                log.warning(f"Season with id {season_id} not found.")
                raise NotFoundError(f"Season with id {season_id} not found.")
            log.info(f"Successfully retrieved season with id: {season_id}")
            return SeasonSchema.model_validate(season)
        except SQLAlchemyError as e:
            log.error(f"Database error while retrieving season {season_id}: {e}")
            raise

    def add_season_request(
        self, season_request: SeasonRequestSchema
    ) -> SeasonRequestSchema:
        """
        Adds a Season to the SeasonRequest table, which marks it as requested.

        :param season_request: The SeasonRequest object to add.
        :return: The added SeasonRequest object.
        :raises IntegrityError: If a similar request already exists or violates constraints.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Adding season request: {season_request.model_dump_json()}")
        db_model = SeasonRequest(
            id=season_request.id,
            season_id=season_request.season_id,
            wanted_quality=season_request.wanted_quality,
            min_quality=season_request.min_quality,
            requested_by_id=season_request.requested_by.id
            if season_request.requested_by
            else None,
            authorized=season_request.authorized,
            authorized_by_id=season_request.authorized_by.id
            if season_request.authorized_by
            else None,
        )
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
            log.info(f"Successfully added season request with id: {db_model.id}")
            return SeasonRequestSchema.model_validate(db_model)
        except IntegrityError as e:
            self.db.rollback()
            log.error(f"Integrity error while adding season request: {e}")
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(f"Database error while adding season request: {e}")
            raise

    def delete_season_request(self, season_request_id: SeasonRequestId) -> None:
        """
        Removes a SeasonRequest by its ID.

        :param season_request_id: The ID of the season request to delete.
        :raises NotFoundError: If the season request is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to delete season request with id: {season_request_id}")
        try:
            stmt = delete(SeasonRequest).where(SeasonRequest.id == season_request_id)
            result = self.db.execute(stmt)
            if result.rowcount == 0:
                log.warning(
                    f"Season request with id {season_request_id} not found during delete execution (rowcount 0)."
                )
            self.db.commit()
            log.info(
                f"Successfully deleted season request with id: {season_request_id}"
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(
                f"Database error while deleting season request {season_request_id}: {e}"
            )
            raise

    def get_season_by_number(self, season_number: int, show_id: ShowId) -> SeasonSchema:
        """
        Retrieve a season by its number and show ID.

        :param season_number: The number of the season.
        :param show_id: The ID of the show.
        :return: A Season object.
        :raises NotFoundError: If the season is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(
            f"Attempting to retrieve season number {season_number} for show_id: {show_id}"
        )
        try:
            stmt = (
                select(Season)
                .where(Season.show_id == show_id)
                .where(Season.number == season_number)
                .options(joinedload(Season.episodes), joinedload(Season.show))
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                log.warning(
                    f"Season number {season_number} for show_id {show_id} not found."
                )
                raise NotFoundError(
                    f"Season number {season_number} for show_id {show_id} not found."
                )
            log.info(
                f"Successfully retrieved season number {season_number} for show_id: {show_id}"
            )
            return SeasonSchema.model_validate(result)
        except SQLAlchemyError as e:
            log.error(
                f"Database error retrieving season {season_number} for show {show_id}: {e}"
            )
            raise

    def get_season_requests(self) -> list[RichSeasonRequestSchema]:
        """
        Retrieve all season requests.

        :return: A list of RichSeasonRequest objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug("Attempting to retrieve all season requests.")
        try:
            stmt = select(SeasonRequest).options(
                joinedload(SeasonRequest.requested_by),
                joinedload(SeasonRequest.authorized_by),
                joinedload(SeasonRequest.season).joinedload(Season.show),
            )
            results = self.db.execute(stmt).scalars().unique().all()
            log.info(f"Successfully retrieved {len(results)} season requests.")
            return [
                RichSeasonRequestSchema(
                    id=x.id,
                    min_quality=x.min_quality,
                    wanted_quality=x.wanted_quality,
                    season_id=x.season_id,
                    show=x.season.show,
                    season=x.season,
                    requested_by=x.requested_by,
                    authorized_by=x.authorized_by,
                    authorized=x.authorized,
                )
                for x in results
            ]
        except SQLAlchemyError as e:
            log.error(f"Database error while retrieving season requests: {e}")
            raise

    def add_season_file(self, season_file: SeasonFileSchema) -> SeasonFileSchema:
        """
        Adds a season file record to the database.

        :param season_file: The SeasonFile object to add.
        :return: The added SeasonFile object.
        :raises IntegrityError: If the record violates constraints.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Adding season file: {season_file.model_dump_json()}")
        db_model = SeasonFile(**season_file.model_dump())
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
            # Assuming SeasonFile model has an 'id' attribute after refresh for logging.
            # If not, this line or the model needs adjustment.
            log.info(
                f"Successfully added season file. Torrent ID: {db_model.torrent_id}, Path: {db_model.file_path_suffix}"
            )
            return SeasonFileSchema.model_validate(db_model)
        except IntegrityError as e:
            self.db.rollback()
            log.error(f"Integrity error while adding season file: {e}")
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(f"Database error while adding season file: {e}")
            raise

    def remove_season_files_by_torrent_id(self, torrent_id: TorrentId) -> int:
        """
        Removes season file records associated with a given torrent ID.

        :param torrent_id: The ID of the torrent whose season files are to be removed.
        :return: The number of season files removed.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to remove season files for torrent_id: {torrent_id}")
        try:
            stmt = delete(SeasonFile).where(SeasonFile.torrent_id == torrent_id)
            result = self.db.execute(stmt)
            self.db.commit()
            deleted_count = result.rowcount  # rowcount is an int, not a callable
            log.info(
                f"Successfully removed {deleted_count} season files for torrent_id: {torrent_id}"
            )
            return deleted_count()
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(
                f"Database error removing season files for torrent_id {torrent_id}: {e}"
            )
            raise

    def set_show_library(self, show_id: ShowId, library: str) -> None:
        """
        Sets the library for a show.

        :param show_id: The ID of the show to update.
        :param library: The library path to set for the show.
        :raises NotFoundError: If the show with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Setting library for show_id {show_id} to {library}")
        try:
            show = self.db.get(Show, show_id)
            if not show:
                log.warning(f"Show with id {show_id} not found.")
                raise NotFoundError(f"Show with id {show_id} not found.")
            show.library = library
            self.db.commit()
            log.info(f"Successfully set library for show_id {show_id} to {library}")
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(f"Database error setting library for show {show_id}: {e}")
            raise

    def get_season_files_by_season_id(
        self, season_id: SeasonId
    ) -> list[SeasonFileSchema]:
        """
        Retrieve all season files for a given season ID.

        :param season_id: The ID of the season.
        :return: A list of SeasonFile objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to retrieve season files for season_id: {season_id}")
        try:
            stmt = select(SeasonFile).where(SeasonFile.season_id == season_id)
            results = self.db.execute(stmt).scalars().all()
            log.info(
                f"Successfully retrieved {len(results)} season files for season_id: {season_id}"
            )
            return [SeasonFileSchema.model_validate(sf) for sf in results]
        except SQLAlchemyError as e:
            log.error(
                f"Database error retrieving season files for season_id {season_id}: {e}"
            )
            raise

    def get_torrents_by_show_id(self, show_id: ShowId) -> list[TorrentSchema]:
        """
        Retrieve all torrents associated with a given show ID.

        :param show_id: The ID of the show.
        :return: A list of Torrent objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to retrieve torrents for show_id: {show_id}")
        try:
            stmt = (
                select(Torrent)
                .distinct()
                .join(SeasonFile, SeasonFile.torrent_id == Torrent.id)
                .join(Season, Season.id == SeasonFile.season_id)
                .where(Season.show_id == show_id)
            )
            results = self.db.execute(stmt).scalars().unique().all()
            log.info(
                f"Successfully retrieved {len(results)} torrents for show_id: {show_id}"
            )
            return [TorrentSchema.model_validate(torrent) for torrent in results]
        except SQLAlchemyError as e:
            log.error(f"Database error retrieving torrents for show_id {show_id}: {e}")
            raise

    def get_all_shows_with_torrents(self) -> list[ShowSchema]:
        """
        Retrieve all shows that are associated with a torrent, ordered alphabetically by show name.

        :return: A list of Show objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug("Attempting to retrieve all shows with torrents.")
        try:
            stmt = (
                select(Show)
                .distinct()
                .join(Season, Show.id == Season.show_id)
                .join(SeasonFile, Season.id == SeasonFile.season_id)
                .join(Torrent, SeasonFile.torrent_id == Torrent.id)
                .options(joinedload(Show.seasons).joinedload(Season.episodes))
                .order_by(Show.name)
            )
            results = self.db.execute(stmt).scalars().unique().all()
            log.info(f"Successfully retrieved {len(results)} shows with torrents.")
            return [ShowSchema.model_validate(show) for show in results]
        except SQLAlchemyError as e:
            log.error(f"Database error retrieving all shows with torrents: {e}")
            raise

    def get_seasons_by_torrent_id(self, torrent_id: TorrentId) -> list[SeasonNumber]:
        """
        Retrieve season numbers associated with a given torrent ID.

        :param torrent_id: The ID of the torrent.
        :return: A list of SeasonNumber objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to retrieve season numbers for torrent_id: {torrent_id}")
        try:
            stmt = (
                select(Season.number)
                .distinct()
                .join(SeasonFile, Season.id == SeasonFile.season_id)
                .where(SeasonFile.torrent_id == torrent_id)
            )
            results = self.db.execute(stmt).scalars().unique().all()
            log.info(
                f"Successfully retrieved {len(results)} season numbers for torrent_id: {torrent_id}"
            )
            return [SeasonNumber(x) for x in results]
        except SQLAlchemyError as e:
            log.error(
                f"Database error retrieving season numbers for torrent_id {torrent_id}: {e}"
            )
            raise

    def get_season_request(
        self, season_request_id: SeasonRequestId
    ) -> SeasonRequestSchema:
        """
        Retrieve a season request by its ID.

        :param season_request_id: The ID of the season request.
        :return: A SeasonRequest object.
        :raises NotFoundError: If the season request is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to retrieve season request with id: {season_request_id}")
        try:
            request = self.db.get(SeasonRequest, season_request_id)
            if not request:
                log.warning(f"Season request with id {season_request_id} not found.")
                raise NotFoundError(
                    f"Season request with id {season_request_id} not found."
                )
            log.info(
                f"Successfully retrieved season request with id: {season_request_id}"
            )
            return SeasonRequestSchema.model_validate(request)
        except SQLAlchemyError as e:
            log.error(
                f"Database error retrieving season request {season_request_id}: {e}"
            )
            raise

    def get_show_by_season_id(self, season_id: SeasonId) -> ShowSchema:
        """
        Retrieve a show by one of its season's ID.

        :param season_id: The ID of the season to retrieve the show for.
        :return: A Show object.
        :raises NotFoundError: If the show for the given season ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to retrieve show by season_id: {season_id}")
        try:
            stmt = (
                select(Show)
                .join(Season, Show.id == Season.show_id)
                .where(Season.id == season_id)
                .options(joinedload(Show.seasons).joinedload(Season.episodes))
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                log.warning(f"Show for season_id {season_id} not found.")
                raise NotFoundError(f"Show for season_id {season_id} not found.")
            log.info(f"Successfully retrieved show for season_id: {season_id}")
            return ShowSchema.model_validate(result)
        except SQLAlchemyError as e:
            log.error(f"Database error retrieving show by season_id {season_id}: {e}")
            raise

    def add_season_to_show(
        self, show_id: ShowId, season_data: SeasonSchema
    ) -> SeasonSchema:
        """
        Adds a new season and its episodes to a show.
        If the season number already exists for the show, it returns the existing season.

        :param show_id: The ID of the show to add the season to.
        :param season_data: The SeasonSchema object for the new season.
        :return: The added or existing SeasonSchema object.
        :raises NotFoundError: If the show is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to add season {season_data.number} to show {show_id}")
        db_show = self.db.get(Show, show_id)
        if not db_show:
            log.warning(f"Show with id {show_id} not found when trying to add season.")
            raise NotFoundError(f"Show with id {show_id} not found.")

        stmt = (
            select(Season)
            .where(Season.show_id == show_id)
            .where(Season.number == season_data.number)
        )
        existing_db_season = self.db.execute(stmt).scalar_one_or_none()
        if existing_db_season:
            log.info(
                f"Season {season_data.number} already exists for show {show_id} (ID: {existing_db_season.id}). Skipping add."
            )
            return SeasonSchema.model_validate(existing_db_season)

        db_season = Season(
            id=season_data.id,
            show_id=show_id,
            number=season_data.number,
            external_id=season_data.external_id,
            name=season_data.name,
            overview=season_data.overview,
            episodes=[
                Episode(
                    id=ep_schema.id,
                    # season_id will be implicitly set by SQLAlchemy relationship
                    number=ep_schema.number,
                    external_id=ep_schema.external_id,
                    title=ep_schema.title,
                )
                for ep_schema in season_data.episodes
            ],
        )

        self.db.add(db_season)
        self.db.commit()
        self.db.refresh(db_season)
        log.info(
            f"Successfully added season {db_season.number} (ID: {db_season.id}) to show {show_id}."
        )
        return SeasonSchema.model_validate(db_season)

    def add_episode_to_season(
        self, season_id: SeasonId, episode_data: EpisodeSchema
    ) -> EpisodeSchema:
        """
        Adds a new episode to a season.
        If the episode number already exists for the season, it returns the existing episode.

        :param season_id: The ID of the season to add the episode to.
        :param episode_data: The EpisodeSchema object for the new episode.
        :return: The added or existing EpisodeSchema object.
        :raises NotFoundError: If the season is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(
            f"Attempting to add episode {episode_data.number} to season {season_id}"
        )
        db_season = self.db.get(Season, season_id)
        if not db_season:
            log.warning(
                f"Season with id {season_id} not found when trying to add episode."
            )
            raise NotFoundError(f"Season with id {season_id} not found.")

        stmt = (
            select(Episode)
            .where(Episode.season_id == season_id)
            .where(Episode.number == episode_data.number)
        )
        existing_db_episode = self.db.execute(stmt).scalar_one_or_none()
        if existing_db_episode:
            log.info(
                f"Episode {episode_data.number} already exists for season {season_id} (ID: {existing_db_episode.id}). Skipping add."
            )
            return EpisodeSchema.model_validate(existing_db_episode)

        db_episode = Episode(
            id=episode_data.id,
            season_id=season_id,
            number=episode_data.number,
            external_id=episode_data.external_id,
            title=episode_data.title,
        )

        self.db.add(db_episode)
        self.db.commit()
        self.db.refresh(db_episode)
        log.info(
            f"Successfully added episode {db_episode.number} (ID: {db_episode.id}) to season {season_id}."
        )
        return EpisodeSchema.model_validate(db_episode)

    def update_show_attributes(
        self,
        show_id: ShowId,
        name: str | None = None,
        overview: str | None = None,
        year: int | None = None,
        ended: bool | None = None,
        continuous_download: bool | None = None,
    ) -> ShowSchema:  # Removed poster_url from params
        """
        Update attributes of an existing show.

        :param show_id: The ID of the show to update.
        :param name: The new name for the show.
        :param overview: The new overview for the show.
        :param year: The new year for the show.
        :param ended: The new ended status for the show.
        :return: The updated ShowSchema object.
        """
        log.debug(f"Attempting to update attributes for show ID: {show_id}")
        db_show = self.db.get(Show, show_id)
        if not db_show:
            log.warning(f"Show with id {show_id} not found for attribute update.")
            raise NotFoundError(f"Show with id {show_id} not found.")

        updated = False
        if name is not None and db_show.name != name:
            db_show.name = name
            updated = True
        if overview is not None and db_show.overview != overview:
            db_show.overview = overview
            updated = True
        if year is not None and db_show.year != year:
            db_show.year = year
            updated = True
        if ended is not None and db_show.ended != ended:
            db_show.ended = ended
            updated = True
        if (
            continuous_download is not None
            and db_show.continuous_download != continuous_download
        ):
            db_show.continuous_download = continuous_download
            updated = True

        if updated:
            self.db.commit()
            self.db.refresh(db_show)
            log.info(f"Successfully updated attributes for show ID: {show_id}")
        else:
            log.info(f"No attribute changes needed for show ID: {show_id}")
        return ShowSchema.model_validate(db_show)

    def update_season_attributes(
        self, season_id: SeasonId, name: str | None = None, overview: str | None = None
    ) -> SeasonSchema:
        """
        Update attributes of an existing season.

        :param season_id: The ID of the season to update.
        :param name: The new name for the season.
        :param overview: The new overview for the season.
        :param external_id: The new external ID for the season.
        :return: The updated SeasonSchema object.
        :raises NotFoundError: If the season is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to update attributes for season ID: {season_id}")
        db_season = self.db.get(Season, season_id)
        if not db_season:
            log.warning(f"Season with id {season_id} not found for attribute update.")
            raise NotFoundError(f"Season with id {season_id} not found.")

        updated = False
        if name is not None and db_season.name != name:
            db_season.name = name
            updated = True
        if overview is not None and db_season.overview != overview:
            db_season.overview = overview
            updated = True

        if updated:
            self.db.commit()
            self.db.refresh(db_season)
            log.info(f"Successfully updated attributes for season ID: {season_id}")
        else:
            log.info(f"No attribute changes needed for season ID: {season_id}")
        return SeasonSchema.model_validate(db_season)

    def update_episode_attributes(
        self, episode_id: EpisodeId, title: str | None = None
    ) -> EpisodeSchema:
        """
        Update attributes of an existing episode.

        :param episode_id: The ID of the episode to update.
        :param title: The new title for the episode.
        :param external_id: The new external ID for the episode.
        :return: The updated EpisodeSchema object.
        :raises NotFoundError: If the episode is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to update attributes for episode ID: {episode_id}")
        db_episode = self.db.get(Episode, episode_id)
        if not db_episode:
            log.warning(f"Episode with id {episode_id} not found for attribute update.")
            raise NotFoundError(f"Episode with id {episode_id} not found.")

        updated = False
        if title is not None and db_episode.title != title:
            db_episode.title = title
            updated = True

        if updated:
            self.db.commit()
            self.db.refresh(db_episode)
            log.info(f"Successfully updated attributes for episode ID: {episode_id}")
        else:
            log.info(f"No attribute changes needed for episode ID: {episode_id}")
        return EpisodeSchema.model_validate(db_episode)

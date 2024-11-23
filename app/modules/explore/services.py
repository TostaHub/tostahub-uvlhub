from app.modules.explore.repositories import ExploreRepository


class ExploreService:
    def __init__(self):
        self.repository = ExploreRepository()

    def filter(self, query: str, sorting="newest", publication_type="any",
               start_date="", end_date="", min_uvl="", max_uvl="", by_valid_uvls="",
               min_num_configurations="", max_num_configurations="", **kwargs):

        return self.repository.filter(query, sorting, publication_type, start_date,
                                      end_date, min_uvl, max_uvl, by_valid_uvls, min_num_configurations,
                                      max_num_configurations, **kwargs)

from python_search.feature_toggle import FeatureToggle


class Report:
    """
    Reponsisble to give an overview of the current state of the application.
    """

    def generate(self):
        return {
            "features": {
                "ranking_latest_used": FeatureToggle().is_enabled("ranking_latest_used")
            }
        }

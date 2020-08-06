from django.urls import path
from gap.views import ActionRunViewSet, ActionDetailViewSet, ActionReleaseCancelViewSet


class AutomateRouter:

    # base_path = 'api/automate/manifest'
    run_view = list_view = ActionRunViewSet
    status_view = ActionDetailViewSet
    release_view = cancel_view = ActionReleaseCancelViewSet

    @property
    def urls(self):
        return [
            path('run', self.run_view.as_view({'post': 'create'})),
            path('list', self.list_view.as_view({'get': 'list'})),
            path('<pk>/status', self.status_view.as_view({'get': 'retrieve'})),
            path('<pk>/cancel', self.cancel_view.as_view({'post': 'cancel'})),
            path('<pk>/release', self.release_view.as_view({'post': 'release'})),
        ]

# TESTING
from gap.views import TransferManifestRunViewSet


class TransferManifestRouter(AutomateRouter):
    run_view = TransferManifestRunViewSet

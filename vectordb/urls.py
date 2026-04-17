from django.urls import path
from .views import VDBUploadView,VectorFileListView, VectorFileDeleteView

urlpatterns = [
    path('upload/', VDBUploadView.as_view(), name='vdb-upload'),
    path("files/", VectorFileListView.as_view(), name="vdb-file-list"),
    path("files/<str:doc_hash>/", VectorFileDeleteView.as_view(), name="vdb-file-delete"),
]

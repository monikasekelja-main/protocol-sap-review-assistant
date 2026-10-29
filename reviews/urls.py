from django.urls import path

from . import views

urlpatterns = [
    path("projects/<uuid:project_id>/members/remove/", views.remove_member, name="remove_member"),
    path("reviews/<uuid:pk>/rerun/", views.rerun, name="rerun"),
    path("", views.home, name="home"),
    path("projects/create/", views.create_project, name="create_project"),
    path("projects/<uuid:project_id>/upload/", views.upload, name="upload"),
    path("projects/<uuid:project_id>/members/", views.add_member, name="add_member"),
    path("projects/<uuid:project_id>/delete/", views.delete_project, name="delete_project"),
    path("reviews/<uuid:pk>/", views.detail, name="review"),
    path("reviews/<uuid:pk>/confirm/", views.confirm, name="confirm"),
    path("reviews/<uuid:pk>/decisions/<int:finding_id>/", views.decision, name="decision"),
    path("reviews/<uuid:pk>/chat/", views.chat, name="chat"),
    path("reviews/<uuid:pk>/propose/", views.propose, name="propose"),
    path(
        "reviews/<uuid:pk>/proposals/<int:proposal_id>/",
        views.accept_proposal,
        name="accept_proposal",
    ),
    path("reviews/<uuid:pk>/report/", views.report, name="report"),
    path("reviews/<uuid:pk>/documents/<int:doc_id>/", views.document, name="document"),
]

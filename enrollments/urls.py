from django.urls import path

from . import views

urlpatterns = [
    path("courses/", views.course_list, name="course_list"),
    path("enroll/<int:section_id>/", views.enroll, name="enroll"),
    path("drop/<int:enrollment_id>/", views.drop, name="drop"),
    path("my-schedule/", views.my_schedule, name="my_schedule"),
]

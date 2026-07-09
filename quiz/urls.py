from django.urls import path
from . import views

urlpatterns = [
    path('',                   views.home,          name='home'),
    path('register/',          views.register,      name='register'),
    path('setup/',             views.quiz_setup,    name='quiz_setup'),
    path('quiz/start/',        views.quiz_start,    name='quiz_start'),
    path('quiz/question/',     views.quiz_question, name='quiz_question'),
    path('quiz/answer/',       views.quiz_answer,   name='quiz_answer'),
    path('quiz/summary/',      views.quiz_summary,  name='quiz_summary'),
    path('history/',           views.history,       name='history'),
    path('history/<int:attempt_id>/', views.history_detail, name='history_detail'),
    path('leaderboard/',       views.leaderboard,   name='leaderboard'),
    path('wrong-review/',      views.wrong_review,  name='wrong_review'),
]

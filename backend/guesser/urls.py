# urls.py
from django.urls import path
from .views import GuessView, QuestionView

app_name = "guesser"

urlpatterns = [
    path("guesser/question", QuestionView.as_view(), name="question"),
    path("guesser/guess", GuessView.as_view(), name="guess"),
]

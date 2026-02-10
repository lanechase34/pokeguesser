# urls.py
from django.urls import path
from .views import GuessView, QuestionView

app_name = "guesser"

urlpatterns = [
    path("question", QuestionView.as_view(), name="question"),
    path("guess", GuessView.as_view(), name="guess"),
]

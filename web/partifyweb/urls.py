from django.conf.urls import url
import partifyweb.views

urlpatterns = [
    url(r'$', partifyweb.views.now_playing),
]

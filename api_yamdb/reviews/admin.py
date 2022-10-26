from django.contrib import admin

from .models import (Categories, Comment, Genres, GenreTitle, Review, Title,
                     User)

admin.site.register(User)
admin.site.register(Categories)
admin.site.register(Genres)
admin.site.register(Title)
admin.site.register(GenreTitle)
admin.site.register(Review)
admin.site.register(Comment)

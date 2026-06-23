from django.contrib import admin

from .models import KaraokeTrack, UserKaraokeAccess


@admin.register(KaraokeTrack)
class KaraokeTrackAdmin(admin.ModelAdmin):
    list_display  = ('id', 'song', 'status', 'processed_at', 'created_at')
    list_filter   = ('status',)
    search_fields = ('song__title',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'processed_at')


@admin.register(UserKaraokeAccess)
class UserKaraokeAccessAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'karaoke_track', 'credits_paid', 'granted_at')
    search_fields = ('user__email', 'karaoke_track__song__title')
    readonly_fields = ('granted_at',)

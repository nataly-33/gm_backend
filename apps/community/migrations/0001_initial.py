import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('songs', '0002_song_ml_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SongLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('song', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='liked_by', to='songs.song')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='song_likes', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at'], 'unique_together': {('user', 'song')}},
        ),
        migrations.CreateModel(
            name='SongPlay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration_seconds', models.IntegerField(default=0)),
                ('played_at', models.DateTimeField(auto_now_add=True)),
                ('song', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plays', to='songs.song')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='song_plays', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-played_at']},
        ),
    ]

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0005_song_lyrics_timestamps'),
    ]

    operations = [
        migrations.RemoveField(model_name='song', name='ml_predicted_genre'),
        migrations.RemoveField(model_name='song', name='ml_predicted_mood'),
        migrations.RemoveField(model_name='song', name='ml_confidence'),
    ]

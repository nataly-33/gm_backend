from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('songs', '0004_song_language'),
    ]
    operations = [
        migrations.AddField(
            model_name='song',
            name='lyrics_timestamps',
            field=models.JSONField(blank=True, null=True),
        ),
    ]

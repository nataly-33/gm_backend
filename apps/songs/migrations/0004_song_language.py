from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0003_song_vocal_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='language',
            field=models.CharField(
                choices=[('es', 'Spanish'), ('en', 'English')],
                default='es',
                max_length=10,
            ),
        ),
    ]

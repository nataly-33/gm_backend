from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='ml_predicted_genre',
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='ml_predicted_mood',
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='ml_confidence',
            field=models.JSONField(blank=True, null=True),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0002_song_ml_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='vocal_type',
            field=models.CharField(
                choices=[('male', 'Male'), ('female', 'Female'), ('auto', 'Auto')],
                default='auto',
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='song',
            name='guidance_scale',
            field=models.FloatField(default=10.0),
        ),
        migrations.AlterField(
            model_name='song',
            name='infer_step',
            field=models.IntegerField(default=100),
        ),
    ]

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('songs', '0002_song_ml_fields'),
        ('stems', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MixProject',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('bpm', models.IntegerField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[('draft','Draft'),('processing','Processing'),('ready','Ready'),('failed','Failed')],
                    default='draft', max_length=20,
                )),
                ('output_s3_key', models.TextField(blank=True, null=True)),
                ('duration_seconds', models.IntegerField(blank=True, null=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mix_projects',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-created_at'], 'abstract': False},
        ),
        migrations.CreateModel(
            name='MixClip',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('position', models.IntegerField()),
                ('start_time_ms', models.IntegerField(default=0)),
                ('end_time_ms', models.IntegerField()),
                ('fade_in_ms', models.IntegerField(default=0)),
                ('fade_out_ms', models.IntegerField(default=0)),
                ('volume', models.FloatField(default=1.0)),
                ('custom_audio_s3_key', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mix_project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='clips',
                    to='mix.mixproject',
                )),
                ('song', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='mix_clips',
                    to='songs.song',
                )),
                ('stem_file', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='mix_clips',
                    to='stems.stemfile',
                )),
            ],
            options={'ordering': ['position']},
        ),
        migrations.CreateModel(
            name='MixExport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('format', models.CharField(
                    choices=[('mp3','MP3'),('wav','WAV')],
                    default='mp3', max_length=10,
                )),
                ('quality', models.CharField(
                    choices=[('128k','128kbps'),('320k','320kbps'),('lossless','Lossless WAV')],
                    default='320k', max_length=10,
                )),
                ('output_s3_key', models.TextField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[('queued','Queued'),('processing','Processing'),('ready','Ready'),('failed','Failed')],
                    default='queued', max_length=20,
                )),
                ('credits_used', models.IntegerField(default=3)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('mix_project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='exports',
                    to='mix.mixproject',
                )),
            ],
            options={'abstract': False},
        ),
    ]

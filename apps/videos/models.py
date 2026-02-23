"""
Video model and HLS processing trigger.

Defines the Video model used in the Videoflix platform and
automatically triggers background HLS conversion after upload.
"""
from django.db import models
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

class Video(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to="thumbnails/")
    category = models.CharField(max_length=100)

    file = models.FileField(
        upload_to="videos/",
        validators=[FileExtensionValidator(allowed_extensions=["mp4"])],
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title

@receiver(post_save, sender=Video)
def trigger_hls_conversion(sender, instance, created, **kwargs):
    if created and instance.file:
        from .tasks import convert_video_to_hls   
        convert_video_to_hls.delay(instance.id)
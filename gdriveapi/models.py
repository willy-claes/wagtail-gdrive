from django.db import models

class SyncMeta(models.Model):
    name = models.CharField(max_length=255)
    value = models.TextField(null=True, blank=True)

    @staticmethod
    def get_value(name, default=None):
        values = SyncMeta.objects.filter(name=name)
        if values.count() == 0:
            if default is None:
                return False
            else:
                return default
        return values[0].value

    @staticmethod
    def set_value(name, value):
        existing = SyncMeta.get_value(name)
        if existing is False:
            meta = SyncMeta(name=name, value=value)
            meta.save()
        else:
            meta = SyncMeta.objects.get(name=name)
            meta.value = value
            meta.save()
    

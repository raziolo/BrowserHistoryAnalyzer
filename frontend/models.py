from django.db import models

# Create your models here.


class HistoryEvent(models.Model):

    url = models.TextField()
    last_visit = models.TextField()
    title = models.TextField()
    visit_count = models.IntegerField()
    category = models.TextField()
    browser = models.TextField()

    def __str__(self):
        return f"HistoryEvent(url={self.url}, last_visit={self.last_visit}, title={self.title}, visit_count={self.visit_count}, category={self.category}, browser={self.browser})"

    class Meta:
        app_label = 'frontend'

class App_Settings(models.Model):
    name = models.CharField(max_length=255, unique=True)
    value = models.JSONField(max_length=255)

    def __str__(self):
        return f"Settings(name={self.name}, value={self.value})"

    class Meta:
        app_label = 'frontend'
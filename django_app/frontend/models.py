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


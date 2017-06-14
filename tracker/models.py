from django.db import models

#bot user details
class bot_user(models.Model):

    facebook_id=models.CharField(max_length=1000)
    first_name=models.CharField(max_length=100)
    last_name=models.CharField(max_length=100)
    profile_pic=models.URLField()
    locale=models.CharField(max_length=1000)
    timezone=models.CharField(max_length=1000)
    gender=models.CharField(max_length=10)
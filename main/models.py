from django.utils import timezone
from django.db import models

# Create your models here.
class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)


class Solvent(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    position = models.FloatField()

class Impurity(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    solvent = models.ForeignKey(Solvent, on_delete=models.SET_NULL, null=True)

class Compound(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

class Spectrum(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    solvent = models.ForeignKey(Solvent, on_delete=models.SET_NULL, null=True)
    compound = models.ForeignKey(Compound, on_delete=models.SET_NULL, null=True)
    formated = models.TextField()
    processed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)


class Peak(models.Model):
    id = models.AutoField(primary_key=True)
    spectrum = models.ForeignKey(Spectrum, on_delete=models.CASCADE)
    ppm = models.FloatField()
    integral_area = models.FloatField()

class Comparison(models.Model):
    spectrum1 = models.ForeignKey(Spectrum, on_delete=models.SET_NULL, null=True,  related_name='comparisons1')
    spectrum2 = models.ForeignKey(Spectrum, on_delete=models.SET_NULL, null=True, related_name='comparisons2')
    similarity_score = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

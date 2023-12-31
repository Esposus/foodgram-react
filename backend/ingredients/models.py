from django.db import models
from django.db.models.constraints import UniqueConstraint


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text='Название ингредиента'
    )
    amount = models.PositiveIntegerField(default=1)
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения',
        help_text='Единица измерения'
    )

    class Meta:
        constraints = [UniqueConstraint(
            fields=['name', 'measurement_unit'],
            name='unique_measurement_unit'
        )]
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'

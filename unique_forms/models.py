from django.db import models


class Design(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Product(models.Model):
    class Types(models.TextChoices):
        MUG = "Mug", "Mug"
        T_SHIRT = "T-Shirt", "T-Shirt"

    class Sizes(models.TextChoices):
        S = "S", "Small"
        M = "M", "Medium"
        L = "L", "Large"
        XL = "XL", "Extra Large"

    design = models.ForeignKey(Design, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=255,
        choices=Types.choices,
        default=Types.T_SHIRT,
    )
    size = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=Sizes.choices,
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
    )

    def __str__(self) -> str:
        if self.size:
            return f"{self.design} {self.type} ({self.size})"
        return f"{self.design} {self.type}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["design", "type"],
                condition=models.Q(size__isnull=True),
                name="unique_design_type",
            ),
            models.UniqueConstraint(
                fields=["design", "type", "size"],
                name="unique_design_type_size",
            ),
        ]

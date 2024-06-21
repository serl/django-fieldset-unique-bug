# Readme

Minimal project to show a possible bug in Django.

**It seems like that `UniqueConstraint` with `condition` are not checked in a `BaseInlineFormSet`.**

The important bits are:

- The `models.py` file, in particular the `unique_design_type` constraint:

    ```python
    class Product(models.Model):
        design = models.ForeignKey(...)
        type = models.CharField(...)
        size = models.CharField(null=True, ...)
        ...

        class Meta:
                constraints = [
                models.UniqueConstraint(
                    fields=["design", "type"],
                    condition=models.Q(size__isnull=True),
                    name="unique_design_type",
                ),
                ...
            ]
    ```

- The `tests.py` file, in particular the `TestFormSetValidation.test_validation_unique_design_type` test case:

    ```python
    def test_validation_unique_design_type(self):
        ...

        formset = FormSet(
            data={
                f"{prefix}-TOTAL_FORMS": "2",
                f"{prefix}-MAX_NUM_FORMS": "1000",
                f"{prefix}-0-type": "Mug",
                f"{prefix}-0-price": "2",
                f"{prefix}-1-type": "Mug",
                f"{prefix}-1-price": "2",
            },
            instance=design,
        )

        # EXPECTED BEHAVIOR
        self.assertFalse(formset.is_valid())
        with self.assertRaisesMessage(ValueError, "didn't validate"):
            formset.save()

        # ACTUAL BEHAVIOR
        # self.assertTrue(formset.is_valid())
        # with self.assertRaisesMessage(IntegrityError, "UNIQUE constraint failed"):
        #     formset.save()
    ```

Note how the validation don't catch the `UniqueConstraint` violation, which gives an `IntegrityError` instead.

In `tests.py`, there are also tests to confirm that the constraint behaves correctly in all the other cases, as long as a constraint without `condition` which works as expected.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

./manage.py test
```

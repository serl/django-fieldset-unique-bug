from unittest.mock import ANY
from django.db import IntegrityError
from django.forms import BaseInlineFormSet, ModelForm
from django.http import HttpRequest
from django.test import TestCase
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User

from .models import Design, Product
from .admin import ProductInlineAdmin, ProductAdmin


class TestUniqueConstraints(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.design = Design.objects.create(name="Design")

    def test_constraint_unique_design_type_error_if_equal(self):
        with self.assertRaises(IntegrityError):
            Product.objects.bulk_create(
                [
                    Product(design=self.design, type=Product.Types.MUG),
                    Product(design=self.design, type=Product.Types.MUG),
                ]
            )

    def test_constraint_unique_design_type_size_error_if_equal(self):
        with self.assertRaises(IntegrityError):
            Product.objects.bulk_create(
                [
                    Product(
                        design=self.design, type=Product.Types.MUG, size=Product.Sizes.S
                    ),
                    Product(
                        design=self.design, type=Product.Types.MUG, size=Product.Sizes.S
                    ),
                ]
            )

    def test_constraint_unique_design_type_size_ok_if_different(self):
        Product.objects.bulk_create(
            [
                Product(
                    design=self.design, type=Product.Types.MUG, size=Product.Sizes.S
                ),
                Product(
                    design=self.design, type=Product.Types.MUG, size=Product.Sizes.L
                ),
            ]
        )

        self.assertEqual(Product.objects.count(), 2)


class TestFormValidation(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.design = Design.objects.create(name="Design")

        cls.http_request = HttpRequest()
        cls.http_request.user = User(is_staff=True, is_superuser=True)

    def get_form_class(self) -> type[ModelForm]:
        return ProductAdmin(
            Product,
            AdminSite(),
        ).get_form(
            self.http_request,
            obj=None,
        )

    def test_validation_without_error(self):
        Form = self.get_form_class()

        form = Form(
            data={
                "design": self.design.pk,
                "type": Product.Types.T_SHIRT,
                "size": Product.Sizes.S,
                "price": 2,
            }
        )

        self.assertTrue(form.is_valid())
        instance = form.save()
        self.assertEqual(instance.design, self.design)

    def test_validation_unique_design_type(self):
        Product.objects.create(
            design=self.design,
            type=Product.Types.MUG,
        )
        Form = self.get_form_class()

        form = Form(
            data={
                "design": self.design.pk,
                "type": Product.Types.MUG,
                "price": 2,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {"__all__": ["Constraint “unique_design_type” is violated."]},
        )
        with self.assertRaisesMessage(ValueError, "didn't validate"):
            form.save()

    def test_validation_unique_design_type_size(self):
        Product.objects.create(
            design=self.design,
            type=Product.Types.T_SHIRT,
            size=Product.Sizes.XL,
        )
        Form = self.get_form_class()

        form = Form(
            data={
                "design": self.design.pk,
                "type": Product.Types.T_SHIRT,
                "size": Product.Sizes.XL,
                "price": 2,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {"__all__": ["Product with this Design, Type and Size already exists."]},
        )
        with self.assertRaisesMessage(ValueError, "didn't validate"):
            form.save()


class TestFormSetValidation(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.design = Design.objects.create(name="Design")
        cls.http_request = HttpRequest()
        cls.http_request.user = User(is_staff=True, is_superuser=True)

    def get_formset_class(self) -> type[BaseInlineFormSet]:
        return ProductInlineAdmin(
            Design,
            AdminSite(),
        ).get_formset(
            request=self.http_request,
            obj=self.design,
        )

    def test_validation_without_error(self):
        FormSet = self.get_formset_class()
        prefix = FormSet().prefix

        formset = FormSet(
            data={
                f"{prefix}-INITIAL_FORMS": "0",
                f"{prefix}-TOTAL_FORMS": "2",
                f"{prefix}-MAX_NUM_FORMS": "1000",
                f"{prefix}-0-type": "Mug",
                f"{prefix}-0-price": "2",
                f"{prefix}-1-type": "T-Shirt",
                f"{prefix}-1-price": "2",
            },
            instance=self.design,
        )

        self.assertEqual(formset.total_form_count(), 2)
        self.assertTrue(formset.is_valid())
        instances = formset.save()
        self.assertEqual(len(instances), 2)

    def test_validation_unique_design_type(self):
        FormSet = self.get_formset_class()
        prefix = FormSet().prefix

        formset = FormSet(
            data={
                f"{prefix}-INITIAL_FORMS": "0",
                f"{prefix}-TOTAL_FORMS": "2",
                f"{prefix}-MAX_NUM_FORMS": "1000",
                f"{prefix}-0-type": "Mug",
                f"{prefix}-0-price": "2",
                f"{prefix}-1-type": "Mug",
                f"{prefix}-1-price": "2",
            },
            instance=self.design,
        )

        self.assertEqual(formset.total_form_count(), 2)

        # EXPECTED BEHAVIOR
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset.errors,
            [
                {},
                {"__all__": [ANY]},
            ],
        )
        with self.assertRaisesMessage(ValueError, "didn't validate"):
            formset.save()

        # ACTUAL BEHAVIOR
        # self.assertTrue(formset.is_valid())
        # with self.assertRaisesMessage(IntegrityError, "UNIQUE constraint failed"):
        #     formset.save()

    def test_validation_unique_design_type_size(self):
        FormSet = self.get_formset_class()
        prefix = FormSet().prefix

        formset = FormSet(
            data={
                f"{prefix}-INITIAL_FORMS": "0",
                f"{prefix}-TOTAL_FORMS": "2",
                f"{prefix}-MAX_NUM_FORMS": "1000",
                f"{prefix}-0-type": "Mug",
                f"{prefix}-0-size": "XL",
                f"{prefix}-0-price": "2",
                f"{prefix}-1-type": "Mug",
                f"{prefix}-1-size": "XL",
                f"{prefix}-1-price": "2",
            },
            instance=self.design,
        )

        self.assertEqual(formset.total_form_count(), 2)

        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset.errors,
            [
                {},
                {"__all__": ["Please correct the duplicate values below."]},
            ],
        )
        with self.assertRaisesMessage(ValueError, "didn't validate"):
            formset.save()

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import format_html, format_html_join

from photologue.models import Gallery, Photo

from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    """Tovar bolimi"""
    name = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children')
    slug = models.SlugField(max_length=100, unique=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Tovar"""
    category = models.ForeignKey(Category, verbose_name="Kategoriya", on_delete=models.CASCADE)
    title = models.CharField("Nomi", max_length=150)
    description = models.TextField("Tavsif")
    price = models.IntegerField("Narx", default=0)
    slug = models.SlugField(max_length=150)
    availability = models.BooleanField("Borligiyokiyogligi", default=True)
    quantity = models.IntegerField("Soni", default=0)
    photo = models.OneToOneField(
        Photo,
        verbose_name="Rasm nomi",
        on_delete=models.SET_NULL,
        null=True)
    gallery = models.ForeignKey(
        Gallery,
        verbose_name="Rasm",
        on_delete=models.SET_NULL,
        null=True,
        blank=True)

    class Meta:
        verbose_name = "Tovar"
        verbose_name_plural = "Tovarlar"

    def __str__(self):
        return self.title


class Cart(models.Model):
    """Savat"""
    session = models.CharField("Foydalanuvchi sessiyasi", max_length=500, null=True, blank=True)
    user = models.ForeignKey(
        User, verbose_name='Mijoz', on_delete=models.CASCADE, null=True, blank=True
    )
    accepted = models.BooleanField(verbose_name='Zakaz qabul qilindo', default=False)

    class Meta:
        verbose_name = 'Savat'
        verbose_name_plural = 'Savatlar'

    def __str__(self):
        return "{}".format(self.user)


class CartItem(models.Model):
    """Savatlardagi tovarlar"""
    cart = models.ForeignKey(
        Cart, verbose_name='Savat', on_delete=models.CASCADE, related_name="cart_item"
    )
    product = models.ForeignKey(Product, verbose_name='Tavar', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField('Soni', default=1)
    price_sum = models.PositiveIntegerField("Jami", default=0)

    class Meta:
        verbose_name = 'Korzinkadagi tovar'
        verbose_name_plural = 'Korzinkadagi tovarlar'

    def save(self, *args, **kwargs):
        self.price_sum = self.quantity * self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        return "{}".format(self.cart)


class Order(models.Model):
    """Zakazlar"""
    cart = models.ForeignKey(Cart, verbose_name='Savat', on_delete=models.CASCADE)
    accepted = models.BooleanField(verbose_name='Zakaz bajarildi', default=False)
    date = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        verbose_name = 'Zakaz'
        verbose_name_plural ='Zakazlar'

    def __str__(self):
        return "{}".format(self.cart)

    def get_table_products(self):
        table_body = format_html_join(
            '\n',
            """<tr>
            <td>{0}</td>
            <td>{1}</td>
            <td>{2}</td>
            <td>{3}</td>
            </tr>""",
            (
                (item.product.title, item.quantity, item.product.price, item.price_sum)
                for item in self.cart.cart_item.all()
            )
        )

        return format_html(
            """
            <table style="width: 100%;">
            <thead>
                <tr>
                    <th class="product-name">Nomi</th>
                    <th class="product-article">Soni</th>
                    <th class="product-quantity">Narxi</th>
                    <th class="product-quantity">Jami</th>
                </tr>
            </thead>
            <tbody>
            {}
            </tbody>
            </table>
            """,
            table_body
        )

    get_table_products.short_description = 'Tovarlar'
    get_table_products.allow_tags = True


@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    """polzavatel uchun savat yaratish"""
    if created:
        Cart.objects.create(user=instance)

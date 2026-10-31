from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver



class CustomUserManager(BaseUserManager):
    """Define a model manager for CustomUser model with both email and username authentication."""

    def _create_user(self, email, username, password=None, **extra_fields):
        """Create and save a CustomUser with the given email, username, and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(self, email, username, password=None, **extra_fields):
        """Create and save a SuperUser with the given email, username, and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, username, password, **extra_fields)

class CustomUser(AbstractUser):
    username = models.CharField(_('username'), max_length=150, unique=True)
    email = models.EmailField(_('email address'), unique=True)
    is_manager = models.BooleanField('Is manager', default=False)
    is_deliveryboy = models.BooleanField('Is deliveryboy', default=False)


    USERNAME_FIELD = 'email'  # Use email for authentication
    REQUIRED_FIELDS = ['username']


    objects = CustomUserManager()
    



class Category(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name



class Fabric(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    COLOR_CHOICES = [
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('black', 'Black'),
        ('white', 'White'),
        ('yellow', 'Yellow'),
    ]

    SIZE_CHOICES = [
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]

    name = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    discount = models.PositiveIntegerField(default=0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)

    # Updated fields
    colors = models.ManyToManyField('Color', blank=True)
    sizes = models.ManyToManyField('Size', blank=True)
    fabric = models.ForeignKey(Fabric, on_delete=models.CASCADE, null=True, blank=True)

    low_stock_warning = models.BooleanField(default=False)
    stock_status = models.CharField(max_length=20, choices=[('in_stock', 'In Stock'), ('out_of_stock', 'Out of Stock')], default='in_stock')

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=5, unique=True)

    def __str__(self):
        return self.name

    




class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='static/products/images/')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"




class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.user.username


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)  # Default to 1 instead of 0
    size = models.CharField(max_length=10, null=True, blank=True,default="S")  # Store size
    color = models.CharField(max_length=20, null=True, blank=True,default="red")  # Store color
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.quantity * self.product.price  # Calculate total cost

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color} ({self.quantity})"





class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, null=True, blank=True)  # New field for phone number
    address = models.CharField(max_length=255)
    zipcode = models.CharField(max_length=10)
    location = models.CharField(max_length=100, null=True, blank=True)
    shipping_method = models.CharField(max_length=50, default='Standard Delivery', null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('completed', 'Completed')], null=True, blank=True)


    def __str__(self):
        return f"Order {self.id} by {self.first_name}"

    def calculate_total_cost(self):
            # Calculate the total cost of the order by summing up the price of all order items
            total = sum(item.price * item.quantity for item in self.items.all())
            self.total_cost = total
            self.save()

class Customization(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]

    WORK_STATUS_CHOICES = [
        ('0%', '0% Completed'),
        ('25%', '25% Completed'),
        ('50%', '50% Completed'),
        ('75%', '75% Completed'),
        ('100%', '100% Completed'),
    ]

    SLEEVE_CHOICES = [
        ('short', 'Short Sleeve'),
        ('long', 'Long Sleeve'),
        ('sleeveless', 'Sleeveless'),
        ('3/4', '3/4 Sleeve'),
    ]

    COLOR_CHOICES = [
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('black', 'Black'),
        ('white', 'White'),
        ('custom', 'Custom Color'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    custom_text = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='customizations/', blank=True, null=True)
    embroidery_pattern = models.CharField(max_length=255, blank=True, null=True)
    customization_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    work_status = models.CharField(max_length=10, choices=WORK_STATUS_CHOICES, default='0%')

    # New Fields
    color = models.CharField(max_length=50, choices=COLOR_CHOICES, default='black')
    custom_color = models.CharField(max_length=50, blank=True, null=True, help_text="Fill only if you chose 'Custom Color'")
    shoulder_width = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="In cm or inches")
    sleeve_type = models.CharField(max_length=20, choices=SLEEVE_CHOICES, default='short')
    sleeve_length = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="In cm or inches")
    waist_width = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="In cm or inches")
    length = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="In cm or inches")

    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, related_name='customizations', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Customization for {self.product.name} by {self.user.username}"



class OrderItem(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('packing', 'Packing'),
        ('shipping', 'Shipping'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
    ]
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    customization = models.ForeignKey(Customization, on_delete=models.CASCADE, null=True, blank=True)  # Added customization field
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, null=True, blank=True)  # Added size field
    color = models.CharField(max_length=20, null=True, blank=True)  # Added color field
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"OrderItem {self.id} - {self.product.name}"

    def get_cost(self):
        """Returns total cost for this item (price * quantity)."""
        return self.price * self.quantity




class Address(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True,primary_key=False,related_name='user_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    zipcode = models.CharField(max_length=10)  # Add this field
    location = models.CharField(max_length=10, null=True, blank=True)  # Add this field

    def __str__(self):
        return self.first_name

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username

# Signal to automatically create Profile when User is created
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Signal to save Profile when User is saved
@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Manager(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    manager_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)  # Manager's department
    password = models.CharField(max_length=50, null=True)  # Avoid storing passwords in plaintext

    def __str__(self):
        return self.manager_name

class Rating(models.Model):
    product = models.ForeignKey(Product, related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)  # 1-5 Star Rating
    review = models.TextField(blank=True, null=True)  # Add text review
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.rating} for {self.product.name} by {self.user.username}"

class Complaint(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("resolved", "Resolved"),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    complaint_text = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Complaint by {self.user.username} - {self.subject}"



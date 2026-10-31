from django.shortcuts import render,redirect
from django.contrib import messages
from .models import Product,Cart,CartItem,CustomUser,OrderItem,Order,Category,Address,ProductImage,Rating,Profile,Manager,Complaint
from django.http import HttpResponseRedirect

from django.http import JsonResponse,HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,get_object_or_404,redirect

from django.contrib.auth import logout
from django.contrib.auth import authenticate,login
from django.contrib.auth import update_session_auth_hash

from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings

from django.db.models import Q
from django.http import HttpResponse
from decimal import Decimal

from django.shortcuts import render, get_object_or_404
from django.shortcuts import render
from django.http import Http404

from .models import Address, CartItem
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Order, OrderItem 
# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse
from django.core.mail import send_mail, EmailMessage
from django.conf import settings


# Create your views here.
from django.shortcuts import render
from django.db.models import Q
from .models import Product, ProductImage, CartItem



def index(request):
    products = Product.objects.prefetch_related('ratings', 'images').all()

    # Group ratings by product
    product_ratings = {}
    for product in products:
        product_ratings[product.id] = product.ratings.all()

    cart_items = []
    total_cart_items = 0
    total_price = 0
    search = request.GET.get('search')

    if search:
        products = products.filter(Q(name__icontains=search))

    for product in products:
        product.discounted_price = product.price - (product.discount if product.discount else 0)

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(cart__user=request.user)
        total_cart_items = cart_items.count()
        for cart_item in cart_items:
            cart_item.total_price = cart_item.product.price * cart_item.quantity
            total_price += cart_item.total_price

    total_amount = total_price if cart_items else 0

    context = {
        'products': products,
        'product_ratings': product_ratings,
        'stars': range(1, 6),
        'total_amount': total_amount,
        'search': search,
        'cart_items': cart_items,
        'total_cart_items': total_cart_items,
    }

    return render(request, 'index.html', context)





def logout_view(request):
    logout(request)
    return redirect(index)

def loginview(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user_obj = CustomUser.objects.filter(email=email).first()

        if not user_obj:
            messages.warning(request, 'Account not found')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        user_authenticated = authenticate(request, username=email, password=password)  # Use username=email

        if not user_authenticated:
            messages.warning(request, 'Invalid password')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        print(f"Authenticated User: {user_authenticated}")

        login(request, user_authenticated)
        return redirect('/')

    return render(request, 'login.html')



def register(request):
    if request.method == 'POST':
        firstname=request.POST.get('firstname')
        lastname=request.POST.get('lastname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if a user with the provided email already exists
        user_exists = CustomUser.objects.filter(email=email).exists()

        if user_exists:
            messages.warning(request, 'User with this email already exists')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        username_exists = CustomUser.objects.filter(username=username).exists()
        if username_exists:
            messages.warning(request, 'User with this username already exists')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))



        # Create a new CustomUser
        user = CustomUser.objects.create(username=username, email=email,first_name=firstname,last_name=lastname)
        user.set_password(password)
        user.save()

        # Redirect to the login page
        return redirect('login')

    # If the request method is not POST, render the registration page
    return render(request, 'register.html')

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(cart__user=request.user)
    total_cart_items = 0
    total_price = 0
    total_discount = 0

    # Calculate price and discount per cart item
    for cart_item in cart_items:
        cart_item.total_price = cart_item.product.price * cart_item.quantity  # Calculate total price per item
        cart_item.total_discount = cart_item.product.discount * cart_item.quantity  # Calculate total discount per item
        
        total_price += cart_item.total_price
        total_discount += cart_item.total_discount

    discounted_amount = total_price - total_discount
    total_cart_items = cart_items.count()

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_discount': total_discount,
        'total_cart_items': total_cart_items,
        'total_amount': total_price,
        'discounted_amount': discounted_amount,
    }
    return render(request, 'cart.html', context)
@login_required
def checkout(request):
    try:
        address = Address.objects.get(user=request.user)
    except Address.DoesNotExist:
        address = None  # Handle case where no address exists for the user

    cart_items = CartItem.objects.filter(cart__user=request.user)
    total_price = 0
    total_discount = 0
    speed_delivery = 16
    normal_delivery = 0

    # Calculate discounts and total price
    for cart_item in cart_items:
        product_discount = cart_item.product.discount or 0  # Ensure there's a fallback if discount is None
        product_price = cart_item.product.price or 0  # Ensure there's a fallback if price is None
        cart_item.total_discount = product_discount * cart_item.quantity
        total_discount += cart_item.total_discount
        cart_item.total_price = product_price * cart_item.quantity
        total_price += cart_item.total_price

    total_carted_items = cart_items.count()
    total_amount = total_price - total_discount
    discounted_amount = total_amount
    final_amount_with_speed = discounted_amount + speed_delivery

    # Populate form data based on whether an address exists
    form_data = {
        'first_name': address.first_name if address else '',
        'last_name': address.last_name if address else '',
        'email': address.email if address else '',
        'address': address.address if address else '',
        'zipcode': address.zipcode if address else '',
    }

    context = {
        'cart_items': cart_items,
        'address': address,
        'form_data': form_data,
        'total_price': total_price,
        'total_discount': total_discount,
        'total_carted_items': total_carted_items,
        'total_amount': total_amount,
        'discounted_amount': discounted_amount,
        'final_amount_with_speed': final_amount_with_speed,
        'speed_delivery': speed_delivery,
        'normal_delivery': normal_delivery
    }
    return render(request, 'checkout.html', context)

@login_required
def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)
    size = request.GET.get("size")
    color = request.GET.get("color")
    quantity = int(request.GET.get("quantity", 1))
    
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Try to get an existing cart item with the same product and size
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, size=size,
        defaults={'color': color, 'quantity': quantity}
    )

    if not created:
        # If color is different, update it
        if cart_item.color != color:
            cart_item.color = color
        
        # Increase quantity
        cart_item.quantity += quantity

    # Update total price
    cart_item.total_price = cart_item.product.price * cart_item.quantity
    cart_item.save()

    messages.success(request, 'Added to the cart')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def remove_from_user(request, cart_item_id):
    cart_item = get_object_or_404(CustomUser, id=cart_item_id)
    cart_item.delete()
    messages.success(request, 'User removed from Manager')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def remove_from_fabric(request, cart_item_id):
    cart_item = get_object_or_404(Fabric, id=cart_item_id)
    cart_item.delete()
    messages.success(request, 'Item removed from Fabric')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def remove_from_category(request, cart_item_id):
    cart_item = get_object_or_404(Category, id=cart_item_id)
    cart_item.delete()
    messages.success(request, 'Item removed from Category')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def remove_from_color(request, cart_item_id):
    cart_item = get_object_or_404(Color, id=cart_item_id)
    cart_item.delete()
    messages.success(request, 'Item removed from Colors')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def update_cart_item(request, item_id):
    try:
        quantity = int(request.POST.get('quantity'))
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.total_price = cart_item.product.price * quantity
            cart_item.save()
            return JsonResponse({'status': 'success', 'message': 'Quantity updated', 'total_price': cart_item.total_price})
        else:
            cart_item.delete()
            return JsonResponse({'status': 'success', 'message': 'Item removed'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def productpage(request, id):
    products = Product.objects.prefetch_related('ratings', 'images').all()

    # Group ratings by product
    product_ratings = {}
    for product in products:
        product_ratings[product.id] = product.ratings.all()
    # Get the product based on the ID
    productpage = Product.objects.get(id=id)
    ratings = productpage.ratings.all()
    total_reviews = ratings.count() 
    colors = Color.objects.all()
 # Count the number of reviews

    # Get all images for the product
    productpageimages = ProductImage.objects.filter(product=productpage)

    faqs = [
        {"question": "What is the return policy?", "answer": "You can return the product within 30 days."},
        {"question": "Does this product come with a warranty?", "answer": "Yes, it includes a 1-year warranty."},
        {"question": "How long does shipping take?", "answer": "Shipping takes 3-5 business days."},
    ]

    context = {
        "ratings": ratings,
        'products': products,
        'product_ratings': product_ratings,
        'stars': range(1, 6),
        "faqs": faqs,
        "colors": colors,
        "product": productpage,
        "productimages": productpageimages,
        "total_reviews": total_reviews,  # _to total review count
    }
    
    return render(request, 'product_page.html', context)


from django.db.models import Q

def shop(request):
    product = Product.objects.all()
    cart_items = CartItem.objects.all()
    total_cart_items = cart_items.count()
    category_obj = Category.objects.all()

    # Sorting by price
    sort_option = request.GET.get('sorted')
    if sort_option == '2':  # High Price → Low Price
        product = product.order_by('-price')
    elif sort_option == '3':  # Low Price → High Price
        product = product.order_by('price')

    # Filtering by search
    search = request.GET.get('search')
    if search:
        product = product.filter(
            Q(name__icontains=search) |
            Q(category__name__icontains=search)
        )

    # Filtering by category
    categories = request.GET.getlist('category')
    if categories:
        product = product.filter(category__name__in=categories)


    # Filtering by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price and max_price:
        product = product.filter(price__gte=min_price, price__lte=max_price)

    # Calculate total price in cart
    total_amount = sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items)

    context = {
        'product': product,
        'category_obj': category_obj,
        'total_amount': total_amount,
        'cart_items': cart_items,
        'total_cart_items': total_cart_items,
        'search': search,
        'categories': categories,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'shop.html', context)

def about(request):
    return render(request,"about.html")

def contact(request):
    return render(request,"contact.html") 
@login_required
def submit_review(request):
    """Handles review submission via AJAX"""
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        rating_value = request.POST.get("rating_value")
        review_text = request.POST.get("review_text", "")

        try:
            product = get_object_or_404(Product, id=product_id)
            rating_value = int(rating_value)

            if rating_value < 1 or rating_value > 5:
                return JsonResponse({"error": "Invalid rating value"}, status=400)

            # Update or create rating and review
            rating, created = Rating.objects.update_or_create(
                user=request.user,
                product=product,
                defaults={"rating": rating_value, "review": review_text}
            )

            return JsonResponse({"message": "Review submitted successfully!", "rating": rating_value, "review": review_text})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def profile_create(request):
    # Check if the user already has a profile
    if Profile.objects.filter(user=request.user).exists():
        return redirect('profile')  # Redirect if profile already exists

    if request.method == 'POST':
        # Get the form data
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        location = request.POST.get('location')

        # Ensure no fields are empty (basic validation)
        if not all([name, phone_number, address, location]):
            return render(request, 'profile_create.html', {
                'error': 'Please fill out all fields.'
            })

        # Create and save the new profile
        profile = Profile(user=request.user, name=name, phone_number=phone_number,
                          address=address, location=location)
        profile.save()
        return redirect('profile')  # Redirect to the relevant page

    return render(request, 'profile_create.html')

@login_required
def edit_profile(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == 'POST':
        # Update profile fields, only if new values are provided
        profile.name = request.POST.get('name', profile.name)
        profile.phone_number = request.POST.get('phone_number', profile.phone_number)
        profile.address = request.POST.get('address', profile.address)
        profile.location = request.POST.get('location', profile.location)

        # Save the updated profile
        profile.save()
        return redirect('profile')  # Redirect to profile view after saving

    return render(request, 'edit_profile.html', {'profile': profile})


@login_required
def profile_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, 'profile.html', {'profile': profile})

@login_required
def view_complaints(request):
    if request.user.is_staff:  # Ensure only admins can view this
        complaints = Complaint.objects.all()
        return render(request, 'view_complaints.html', {'complaints': complaints})
    else:
        messages.error(request, "You are not authorized to view complaints.")
        return redirect('index')

@login_required
def track_complaint(request, complaint_id):
    if request.user.is_staff:  # Ensure only admins can view and respond
        complaint = get_object_or_404(Complaint, pk=complaint_id)

        if request.method == "POST":
            status = request.POST.get('status')
            admin_response = request.POST.get('admin_response')
            
            if status in dict(Complaint.STATUS_CHOICES).keys():
                complaint.status = status
            if admin_response:
                complaint.admin_response = admin_response
                
            complaint.save()
            messages.success(request, "Complaint updated successfully.")
            return redirect('view_complaints')
        
        return render(request, 'track_complaint.html', {'complaint': complaint})
    else:
        messages.error(request, "You are not authorized to track complaints.")
        return redirect('home')

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Complaint,Color,Size
from django.contrib.auth.decorators import login_required

# View to add a complaint
@login_required
def add_complaint(request):
    if request.method == "POST":
        subject = request.POST.get('subject')
        complaint_text = request.POST.get('complaint_text')

        complaint = Complaint.objects.create(
            user=request.user,
            subject=subject,
            complaint_text=complaint_text,
        )

        messages.success(request, "Your complaint has been submitted successfully.")
        return redirect('user_complaints')  # Redirect to user complaints list

    return render(request, 'add_complaint.html')

# View to list user complaints and admin responses
@login_required
def user_complaints(request):
    complaints = Complaint.objects.filter(user=request.user)  # Only fetch complaints submitted by the logged-in user
    return render(request, 'user_complaints.html', {'complaints': complaints})

def add_product(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        price = request.POST.get("price")
        category_id = request.POST.get("category")
        fabric_id = request.POST.get("fabric")
        discount = request.POST.get("discount", 0)
        stock_quantity = request.POST.get("stock_quantity")

        # Handling multiple selections for colors and sizes
        color_ids = request.POST.getlist("colors")  # List of selected color IDs
        size_ids = request.POST.getlist("sizes")  # List of selected size IDs

        product = Product.objects.create(
            name=name,
            user=request.user,
            description=description,
            price=price,
            category_id=category_id,
            fabric_id=fabric_id,
            discount=discount,
            stock_quantity=stock_quantity,
        )
        images = request.FILES.getlist("images")  # Get multiple uploaded images
        for image in images:
            ProductImage.objects.create(product=product, image=image)

        

        # Assign selected colors and sizes to the product
        product.colors.set(color_ids)
        product.sizes.set(size_ids)
        
        product.save()
        messages.success(request, "Product added successfully!")
        return redirect("product-list")

    categories = Category.objects.all()
    fabrics = Fabric.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.all()

    return render(
        request,
        "add_product.html",
        {"categories": categories, "fabrics": fabrics, "colors": colors, "sizes": sizes},
    )


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category,Fabric

@login_required
def add_category(request):
    """View to add a new category."""
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Category.objects.create(name=name)
            messages.success(request, "Category added successfully!")
            return redirect("add_category")
        else:
            messages.error(request, "Category name cannot be empty.")

    categories = Category.objects.all()
    return render(request, "add_category.html", {"categories": categories})

@login_required
def add_color(request):
    """View to add a new category."""
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Color.objects.create(name=name)
            messages.success(request, "Color added successfully!")
            return redirect("add_color")
        else:
            messages.error(request, "Color name cannot be empty.")

    categories = Color.objects.all()
    return render(request, "add_color.html", {"categories": categories})

@login_required
def add_fabric(request):
    """View to add a new fabric."""
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Fabric.objects.create(name=name)
            messages.success(request, "Fabric added successfully!")
            return redirect("add_fabric")
        else:
            messages.error(request, "Fabric name cannot be empty.")

    fabric = Fabric.objects.all()
    return render(request, "add_fabric.html", {"fabric": fabric})



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, ProductImage, Category

@login_required
def update_product(request, product_id):
    """Update an existing product."""
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.description = request.POST.get("description")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")
        product.stock_quantity = request.POST.get("stock_quantity")
        
        category_id = request.POST.get("category")

        product.category = Category.objects.get(id=category_id) if category_id else None
        
        product.save()
        
        # Handle image updates
        images = request.FILES.getlist("images")
        for image in images:
            ProductImage.objects.create(product=product, image=image)

        messages.success(request, "Product updated successfully!")
        return redirect("product-list")

    categories = Category.objects.all()
    return render(request, "update_product.html", {"product": product, "categories": categories})


@login_required
def delete_product(request, product_id):
    """Delete an existing product."""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect("product-list")

    return render(request, "delete_product.html", {"product": product})


# models.py

# views.py
from django.shortcuts import render, redirect
from .models import Product
from django.http import JsonResponse

@login_required
def product_list(request):
    """Display a list of all products."""
    products = Product.objects.all()

    if request.method == 'POST' and 'product_id' in request.POST:
        product_id = request.POST['product_id']
        try:
            product = Product.objects.get(id=product_id)
            product.low_stock_warning = True  # Set the low stock warning flag
            product.save()
            return JsonResponse({'status': 'success'})
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'})

    return render(request, "product_list.html", {
        "products": products
    })


from django.http import JsonResponse

@login_required
def product_stock_status(request):
    if request.method == "POST":
        product_id = request.POST.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
            # Check if the product is out of stock
            if product.stock_quantity <= 0:
                product.stock_status = 'out_of_stock'
            else:
                product.stock_status = 'in_stock'

            product.save()

            return JsonResponse({'status': 'success', 'message': 'Product stock status updated', 'stock_status': product.stock_status})
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})




from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cart, CartItem, Order, OrderItem

@login_required
def start_order(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        zipcode = request.POST.get('zipcode')
        location = request.POST.get('location')
        shipping_option = request.POST.get('shipping-option', 'Standard Delivery')

        # Convert float to Decimal
        speed_delivery_cost = Decimal('16.00') if shipping_option == 'Speed Delivery' else Decimal('0.00')

        # Fetch the cart associated with the current user
        user_cart = Cart.objects.filter(user=request.user).first()
        if not user_cart:
            messages.error(request, "No cart found for this user.")
            return redirect('cart')

        cart_items = CartItem.objects.filter(cart=user_cart)
        if not cart_items.exists():
            messages.error(request, "No items in cart.")
            return redirect('cart')

        # Calculating total price from cart items using Decimal for all arithmetic
        total_price = sum(Decimal(item.product.price) * item.quantity for item in cart_items)
        total_discount = sum(Decimal(item.product.discount) * item.quantity for item in cart_items)
        total_cost = total_price - total_discount + speed_delivery_cost

        # Create Order
        try:
            order = Order.objects.create(
                user=request.user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                address=address,
                zipcode=zipcode,
                location=location,
                shipping_method=shipping_option,
                shipping_cost=speed_delivery_cost,
                total_cost=total_cost
            )

            # Create OrderItems and update product stock
            for item in cart_items:
                product = item.product
                if product.stock_quantity >= item.quantity:
                    order_item = OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=Decimal(product.price) * item.quantity,
                        quantity=item.quantity,
                        size=item.size,  # ✅ Storing Size
                        color=item.color,  # ✅ Storing Color
                    )
                    # Update product stock quantity
                    product.stock_quantity -= item.quantity
                    product.save()
                else:
                    messages.warning(request, f"Not enough stock for product: {product.name}")
                    return redirect('cart')

            # Clear the cart
            cart_items.delete()
            messages.success(request, "Order placed successfully!")
            return redirect('wishlist')

        except Exception as e:
            messages.error(request, f"An error occurred while placing the order: {e}")
            return redirect('cart')

    return render(request, 'cart.html')


@login_required
def wishlist(request):
    return render(request, 'payment.html')

def vworder(request):
    product_images = ProductImage.objects.all()
    
    # For buyers: List OrderItems linked to Orders made by the user
    buyer_orders = OrderItem.objects.filter(order__user=request.user, customization__isnull=True).order_by('-created_at')


    # For sellers: List OrderItems linked to Products managed by the user
    seller_orders = OrderItem.objects.filter(customization__isnull=True).order_by('-created_at')


    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('action')

        if order_id:
            order = get_object_or_404(OrderItem, pk=order_id)
            if new_status in [status[0] for status in OrderItem.STATUS_CHOICES]:  # Check if new status is valid
                order.status = new_status
                order.save()
                messages.success(request, f"Order status updated to {new_status}.")
                return redirect('order')  # Make sure this matches your URL name
        else:
            messages.error(request, "Order ID not provided.")

    return render(request, 'order.html', {'buyer_orders': buyer_orders, 'seller_orders': seller_orders, 'product_images': product_images})

def cworder(request):
    product_images = ProductImage.objects.all()
    
    # For buyers: List OrderItems linked to Orders made by the user
    buyer_orders = OrderItem.objects.filter(order__user=request.user, customization__isnull=False).order_by('-created_at')

    # For sellers: List OrderItems linked to Products managed by the user
    seller_orders = OrderItem.objects.filter(customization__isnull=False).order_by('-created_at')

    # For managers (superusers): List all customized OrderItems
    custom_orders = Customization.objects.all().order_by('-created_at')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('action')

        if order_id:
            order = get_object_or_404(OrderItem, pk=order_id)
            if new_status in [status[0] for status in OrderItem.STATUS_CHOICES]:  # Check if new status is valid
                order.status = new_status
                order.save()
                messages.success(request, f"Order status updated to {new_status}.")
                return redirect('corder')  # Make sure this matches your URL name
        else:
            messages.error(request, "Order ID not provided.")

    return render(request, 'corder.html', {
        'buyer_orders': buyer_orders, 
        'seller_orders': seller_orders, 
        # 'manager_orders': manager_orders, 
        'product_images': product_images,
        'custom_orders': custom_orders,
    })


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Customization

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Customization

def manager_custom_orders(request):
    if not request.user.is_manager:
        return render(request, "403.html")  # Restrict unauthorized users

    if request.method == "POST":
        customization_id = request.POST.get("customization_id")
        new_work_status = request.POST.get("work_status")  

        if customization_id:
            order = get_object_or_404(Customization, pk=customization_id)

            # Ensure new_work_status is valid
            if new_work_status in [status[0] for status in Customization.WORK_STATUS_CHOICES]:  
                order.work_status = new_work_status  # ✅ Correctly update work_status
                order.save()
                messages.success(request, f"Order work status updated to {new_work_status}.")
                return redirect('manager_custom_orders')
            else:
                messages.error(request, "Invalid work status selected.")
        else:
            messages.error(request, "Customization ID not provided.")

    custom_orders = Customization.objects.all().order_by('-created_at')
    return render(request, "manager_custom_orders.html", {"custom_orders": custom_orders})






@login_required
def address(request):
    try:
        address = Address.objects.get(user=request.user)  # Get the unique address for the user
    except Address.DoesNotExist:
        address = None  # If no address exists, set address to None

    if request.method == "POST":
        # Fetch data from form
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        address_field = request.POST.get('address')  # Avoid name conflict with 'address' variable
        zipcode = request.POST.get('zipcode')
        location = request.POST.get('location')

        if address:
            # Update existing address
            address.first_name = first_name
            address.last_name = last_name
            address.email = email
            address.address = address_field
            address.zipcode = zipcode
            address.location = location
            address.save()
            messages.success(request, 'Address updated successfully!')
        else:
            # Create new address if none exists
            Address.objects.create(user=request.user, first_name=first_name, last_name=last_name, email=email, address=address_field, zipcode=zipcode,location=location)
            messages.success(request, 'Address added successfully!')

        return redirect('address')  # Redirect to the same page to avoid resubmission of form

    # Prepare form data if address exists; otherwise, use empty strings
    form_data = {
        'first_name': address.first_name if address else '',
        'last_name': address.last_name if address else '',
        'email': address.email if address else '',
        'address': address.address if address else '',
        'zipcode': address.zipcode if address else '',
        'location': address.location if address else '',
    }

    return render(request, 'address.html', {'address': address, 'form_data': form_data})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Customization, Order
from django.contrib import messages

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Customization, Order, OrderItem

from decimal import Decimal

@login_required
def customize_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        custom_text = request.POST.get('custom_text')
        embroidery_pattern = request.POST.get('embroidery_pattern')
        image = request.FILES.get('image')
        color = request.POST.get('color')
        custom_color = request.POST.get('custom_color')
        shoulder_width = request.POST.get('shoulder_width')
        sleeve_type = request.POST.get('sleeve_type')
        sleeve_length = request.POST.get('sleeve_length')
        waist_width = request.POST.get('waist_width')
        length = request.POST.get('length')

        order, created = Order.objects.get_or_create(user=request.user, status='pending')

        customization = Customization.objects.create(
            user=request.user,
            product=product,
            custom_text=custom_text,
            embroidery_pattern=embroidery_pattern,
            image=image,
            color=color,
            custom_color=custom_color if color == 'custom' else '',
            shoulder_width=shoulder_width,
            sleeve_type=sleeve_type,
            sleeve_length=sleeve_length,
            waist_width=waist_width,
            length=length,
            order=order
        )

        messages.success(request, "Customization request submitted successfully!")
        return redirect('customization_status')

    return render(request, 'customize_product.html', {'product': product})



# views.py
from django.shortcuts import render, get_object_or_404
from .models import Customization, Order

@login_required
def customization_status(request):
    customizations = Customization.objects.filter(user=request.user)

    # Fetch all orders for the user
    orders = Order.objects.filter(user=request.user)

    # Calculate total price for each customization
    for customization in customizations:
        customization.total_price = customization.product.price + customization.customization_price

    return render(request, 'customization_status.html', {
        'customizations': customizations,
        'orders': orders,  # Pass all orders
    })




@login_required
def admin_customization_list(request):
    customizations = Customization.objects.all().order_by('-created_at') # You can filter by status if needed
    return render(request, 'admin_customization_list.html', {'customizations': customizations})


@login_required
def approve_customization(request, customization_id):
    customization = get_object_or_404(Customization, id=customization_id)
    if request.method == "POST":
        customization_price = request.POST.get('customization_price')
        customization.customization_price = customization_price
        customization.status = 'approved'
        customization.save()
        messages.success(request, "Customization approved successfully!")
        return redirect('admin_customization_list')  # Redirect to the list page after approval

    return render(request, 'approve_customization.html', {'customization': customization})

def reject_customization(request, customization_id):
    customization = get_object_or_404(Customization, id=customization_id)
    customization.status = 'rejected'
    customization.save()
    messages.error(request, "Customization rejected.")
    return redirect('admin_customization_list')


@login_required
def pay_customization(request, customization_id):
    customization = get_object_or_404(Customization, id=customization_id)
    
    # Ensure customization is approved before processing payment
    if not customization.approved:
        messages.error(request, 'This customization cannot be paid for as it is not approved.')
        return redirect('index')  # Redirect back to the index page or any other page as needed

    # Provide a checkout link if customization is approved
    return redirect('customization_details', customization_id=customization.id)

def customization_details(request, customization_id):
    customization = get_object_or_404(Customization, id=customization_id)
    # Retrieve the order associated with the user (this assumes there’s a pending order)
    order = get_object_or_404(Order, user=request.user, status='pending')
    return render(request, 'customize_checkout.html', {
        'customization': customization,
        'order': order
    })


@login_required
def customization_list_with_payment(request):
    customizations = Customization.objects.filter(user=request.user, status='approved')  # Only show approved customizations
    return render(request, 'customization_list_with_payment.html', {'customizations': customizations})



# views.py
from django.shortcuts import render, get_object_or_404
from .models import Customization, Order, Product

from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, Customization, OrderItem

@login_required
def checkouting(request, order_id, customization_id):
    try:
        address = Address.objects.get(user=request.user)
    except Address.DoesNotExist:
        address = None  # Handle case where no address exists for the user
    order = get_object_or_404(Order, id=order_id)
    customization = get_object_or_404(Customization, id=customization_id)

    # Ensure the product associated with customization exists
    product = customization.product

    # Calculate the total price (product price + customization price)
    total_price = product.price + customization.customization_price

    try:
        address = Address.objects.get(user=request.user)
    except Address.DoesNotExist:
        address = None  # Handle case where no address exists for the user

    total_discount = 0
    speed_delivery = 16
    normal_delivery = 0

    # Calculate discounts and total price for cart items
    # ... (your logic for discounts, if needed)

    # Populate form data based on whether an address exists
    form_data = {
        'first_name': address.first_name if address else '',
        'last_name': address.last_name if address else '',
        'email': address.email if address else '',
        'address': address.address if address else '',
        'zipcode': address.zipcode if address else '',
    }

    # Handle form submission
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))  # Default to 1 if not provided
        size = request.POST.get('size')
        color = request.POST.get('color')

        # Create an OrderItem and attach the customization
        order_item = OrderItem(
            order=order,
            product=product,
            price=total_price,
            customization=customization,
            quantity=quantity,
            size=size,
            color=color
        )
        order_item.save()

        # Optionally, update order total cost
        order.calculate_total_cost()

        # Update customization status to 'paid' since order has been placed
        customization.status = 'paid'
        customization.save()

        # Decrease the stock quantity of the product
        if product.stock_quantity > 0:
            product.stock_quantity -= 1
            product.save()

        # Redirect to the order page after placing the order
        return redirect('corder')

    # Return context to render in template
    context = {
        'address': address,
        'form_data': form_data,
        'customization': customization,
        'product': product,
        'order': order,
        'total_price': total_price,
        'total_discount': total_discount,
    }


    return render(request, 'customize_checkout.html', context)









@login_required
def order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST" and request.user.is_superuser:
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()
            messages.success(request, 'Order status updated successfully.')

    # Define status choices for the admin to select from
    status_choices = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    return render(request, 'order_status.html', {
        'order': order,
        'status_choices': status_choices
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import Order

def update_order_status(request, order_id):
    # Ensure the user is an admin
    if not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to update the order status.")

    # Get the order object
    order = get_object_or_404(Order, id=order_id)

    # If it's a POST request, update the status
    if request.method == 'POST':
        status = request.POST.get('status')
        if status:
            order.status = status
            order.save()
            return redirect('order_status', order_id=order.id)  # Redirect to order status page after update

    # Get the available choices for the status (assuming status is a field in your model)
    status_choices = Order.STATUS_CHOICES  # Adjust according to your actual choices in the Order model
    return render(request, 'your_template_name.html', {
        'order': order,
        'status_choices': status_choices,
    })


from .models import CustomUser, Manager

@login_required
def add_manager(request):
    if request.method == "POST":
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        department = request.POST.get('department')
        password = request.POST.get('password')

        # Check if username or email already exists
        if CustomUser.objects.filter(username=username).exists():
            messages.warning(request, 'Username already exists')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if CustomUser.objects.filter(email=email).exists():
            messages.warning(request, 'Email already exists')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # Create a CustomUser instance
        user_ob = CustomUser.objects.create_user(username=username, email=email, password=password, is_manager=True)

        # Create a Manager instance associated with the CustomUser
        manager = Manager.objects.create(
            user=user_ob,
            manager_name=name,
            email=email,
            department=department,
            password=password  # Consider encrypting passwords
        )

        messages.success(request, 'Manager added successfully')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    manageruser=CustomUser.objects.filter(is_manager=True)
    context={
        "managerusers":manageruser,
    }
    return render(request, 'add_manager.html',context)


@login_required
def ChangePassword(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        # Check if the old password is correct
        if not authenticate(request, username=user.username, password=old_password):
            messages.error(request, 'Incorrect old password.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # Check if the new password and confirm password match
        if new_password != confirm_password:
            messages.error(request, 'New password and confirm password do not match.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # Update the user's password
        user.set_password(new_password)
        user.save()

        # Update the session to prevent the user from being logged out
        update_session_auth_hash(request, user)

        messages.success(request, 'Password successfully changed.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request,'changepassword.html')







































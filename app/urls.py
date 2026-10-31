from django.urls import path
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('login/', views.loginview, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),

    path('add/<int:id>/',views.add_to_cart,name='add'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove/<int:cart_item_id>/',views.remove_from_cart,name='remove'),
    path('fabric/remove/<int:cart_item_id>/',views.remove_from_fabric,name='remove_fab'),
    path('category/remove/<int:cart_item_id>/',views.remove_from_category,name='remove_cat'),
    path('color/remove/<int:cart_item_id>/',views.remove_from_color,name='remove_color'),
    path('user/remove/<int:cart_item_id>/',views.remove_from_user,name='remove_user'),

    path('shop/', views.shop, name='shop'),
    path('product-page/<int:id>', views.productpage, name='product-page'),
    path("submit-review/", views.submit_review, name="submit_review"),

    path('profile/create/', views.profile_create, name='profile_create'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/', views.profile_view, name='profile'),

    path('complaints/', views.view_complaints, name='view_complaints'),  # View all complaints
    path('complaint/<int:complaint_id>/', views.track_complaint, name='track_complaint'),
    path('add-complaint/', views.add_complaint, name='add_complaint'),  # Route for adding complaint
    path('my-complaints/', views.user_complaints, name='user_complaints'),
    
    path("add-product/", views.add_product, name="add_product"),
    path("add-category/", views.add_category, name="add_category"),
    path("add-color/", views.add_color, name="add_color"),
    path("add-fabric/", views.add_fabric, name="add_fabric"),
    path("update-product/<int:product_id>/", views.update_product, name="update-product"),
    path("delete-product/<int:product_id>/", views.delete_product, name="delete-product"),
    path("products/", views.product_list, name="product-list"),

    path('start_order', views.start_order,name='start_order'),
    path('wishlist', views.wishlist,name='wishlist'),
    path('about', views.about,name='about'),
    path('contact', views.contact,name='contact'),
    path('vworder', views.vworder,name="order"),
    path('customized/order', views.cworder,name="corder"),

    path("manager/custom-orders/", views.manager_custom_orders, name="manager_custom_orders"),


    path('address/', views.address,name="address"),

    path('update-stock-status/', views.product_stock_status, name='update-stock-status'),

    path('customize/<int:product_id>/', views.customize_product, name='customize_product'),
    path('customization_status/', views.customization_status, name='customization_status'),
    path('admins/customizations/', views.admin_customization_list, name='admin_customization_list'),
    path('approve_customization/<int:customization_id>/', views.approve_customization, name='approve_customization'),
        # path('approve/<int:customization_id>/', approve_customization, name='approve_customization'),
    path('reject/<int:customization_id>/', views.reject_customization, name='reject_customization'),

    path('pay_customization/<int:customization_id>/', views.pay_customization, name='pay_customization'),
    path('customization/<int:customization_id>/', views.customization_details, name='customization_details'),  # Can be removed
    path('checkout/<int:order_id>/<int:customization_id>/', views.checkouting, name='checkouted'),
    path('order_status/<int:order_id>/', views.order_status, name='order_status'),
    path('update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),


    path('add-manager/', views.add_manager, name='add_manager'),

    path('changepassword/',views.ChangePassword,name='change-password'),

]

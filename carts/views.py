from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required


# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()

    return cart


def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    if current_user.is_authenticated:
        product_variations = []
        if request.method == 'POST':
            for key in request.POST:
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key,
                                                      variation_value__iexact=value)
                    product_variations.append(variation)
                except:
                    pass

        is_cart_items_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        if is_cart_items_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variations in ex_var_list:
                index = ex_var_list.index(product_variations)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.cart_quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(product=product, cart_quantity=1, user=current_user)
                if len(product_variations) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variations)
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                cart_quantity=1,
                user=current_user,
            )
            if len(product_variations) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variations)
            cart_item.save()
        return redirect('cart')
    else:
        product_variations = []
        if request.method == 'POST':
            for key in request.POST:
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key,
                                                      variation_value__iexact=value)
                    product_variations.append(variation)
                except:
                    pass

        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))

        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=_cart_id(request)
            )
            cart.save()

        is_cart_items_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if (is_cart_items_exists):
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            print(ex_var_list, product_variations)

            if product_variations in ex_var_list:
                index = ex_var_list.index(product_variations)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.cart_quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(product=product, cart_quantity=1, cart=cart)
                if len(product_variations) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variations)
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                cart_quantity=1,
                cart=cart,
            )
            if len(product_variations) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variations)
            cart_item.save()
        return redirect('cart')


def remove_cart(request, product_id, cart_item_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)
    try:
        if current_user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=current_user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.cart_quantity > 1:
            cart_item.cart_quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass

    return redirect('cart')


def remove_cart_item(request, product_id, cart_item_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)
    if current_user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=current_user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.cart_quantity)
            quantity += cart_item.cart_quantity

        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
    }

    return render(request, 'store/cart.html', context)


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.cart_quantity)
            quantity += cart_item.cart_quantity

        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass
    
    first_name = request.user.first_name
    last_name = request.user.last_name
    email = request.user.email
    phone_number = request.user.phone_number
    address_line_1 = request.user.userprofile.address_line_1
    address_line_2 = request.user.userprofile.address_line_2
    city = request.user.userprofile.city
    state = request.user.userprofile.state
    country = request.user.userprofile.country
    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
        "first_name":first_name,
        "last_name":last_name,
        "email":email,
        "address_line_1":address_line_1,
        "address_line_2":address_line_2,
        "city":city,
        "state":state,
        "country":country,
    }
    return render(request, 'store/checkout.html', context)

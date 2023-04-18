from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from .models import Category, Product, Review, FavouriteProducts, Mail, Customer, Order, OrderProduct, ShippingAddress
from random import randint
from .forms import LoginForm, RegistrationForm, ReviewForm, CustomerForm, ShippingForm

from django.contrib.auth import login, logout
from django.contrib import messages
from shop import settings
from django.core.mail import send_mail
from .utils import CartForAuthenticatedUser, get_cart_data
import stripe

# Create your views here.

class ProductList(ListView):
    model = Product
    context_object_name = 'categories'

    extra_context = {
        'title': 'TOTEMBO: Главная страница'
    }

    def get_queryset(self):
        categories = Category.objects.filter(parent=None)

        return categories

    template_name = 'store/product_list.html'



class CategoryView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'store/category_page.html'

    def get_queryset(self):
        sort_field = self.request.GET.get('sort')
        type_field = self.request.GET.get('type')
        if type_field:
            products = Product.objects.filter(category__slug=type_field)
            return products

        main_category = Category.objects.get(slug=self.kwargs['slug'])  # Родителя (Часы)
        subcategories = main_category.subcategories.all()  # Детей подкатегории (Автоматические и Механические)
        products = Product.objects.filter(category__in=subcategories)  # получаем продукты Детей
        if sort_field:
            products = products.order_by(sort_field)
        return products

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        main_category = Category.objects.get(slug=self.kwargs['slug'])
        context['category'] = main_category
        context['title'] = f'Категория: {main_category.title}'
        return context


class ProductDetail(DetailView):  # product_detail.html
    model = Product
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        product = Product.objects.get(slug=self.kwargs['slug'])
        context['title'] = f'Товар: {product.title}, {product.category}'

        products = Product.objects.all()
        data = []

        for i in range(4):
            random_index = randint(0, len(products)-1)
            product = products[random_index]
            if product not in data:
                data.append(product)
        context['products'] = data

        context['reviews'] = Review.objects.filter(product=product)

        if self.request.user.is_authenticated:
            context['review_form'] = ReviewForm()

        return context


def login_registration(request):
    context = {
        'title': 'Войти или Зарегистрироваться',
        'login_form': LoginForm(),
        'registration_form': RegistrationForm()
    }
    return render(request, 'store/login_registration.html', context)



def user_login(request):
    form = LoginForm(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, 'Успешный вход в Аккаунт')
        return redirect('product_list')
    else:
        messages.error(request, 'Не верный логин или пароль')
        return redirect('login_registration')

def user_logout(request):
    logout(request)
    messages.warning(request, 'Вы вышли из аккаунта')
    return redirect('product_list')


def register(request):
    form = RegistrationForm(data=request.POST)
    if form.is_valid():
        user = form.save()
        messages.success(request, 'Регистрация прошла успешно, войдите в Аккаунт')
    else:
        for field in form.errors:
            messages.error(request, form.errors[field].as_text())

    return redirect('login_registration')




def save_review(request, product_slug):
    form = ReviewForm(data=request.POST)
    product = Product.objects.get(slug=product_slug)
    if form.is_valid():
        review = form.save(commit=False)
        review.author = request.user
        review.product = product
        review.save()
    else:
        pass
    return redirect('product_detail', product.slug)




def save_favourite_products(request, product_slug):
    user = request.user if request.user.is_authenticated else None # получаем запрос если есть Авторизация
    product = Product.objects.get(slug=product_slug)
    fav_products = FavouriteProducts.objects.filter(user=user)
    if user:
        if product in [i.product for i in fav_products]:
            fav_product = FavouriteProducts.objects.get(user=user, product=product)
            messages.warning(request, 'Продукт был удалён из избранного')
            fav_product.delete()
        else:
            messages.success(request, 'Продукт добавлен в избранное')
            FavouriteProducts.objects.create(user=user, product=product)
    else:
        messages.warning(request, 'Выполните вход или регистрацию что бы добавить товар в избранное')


    next_page = request.META.get('HTTP_REFERER', 'product_list')
    return redirect(next_page)


class FavouriteProductsView(LoginRequiredMixin, ListView):
    model = FavouriteProducts
    context_object_name = 'products'
    template_name = 'store/favourite_products.html'
    login_url = 'login_registration'
    permission_denied_message = "Выполните вход или регистрацию что бы перейти на страницу избранного"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, self.permission_denied_message)
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        favs = FavouriteProducts.objects.filter(user=user)
        products = [i.product for i in favs]
        return products



def save_mail(request):
    email = request.POST.get('email')
    user = request.user if request.user.is_authenticated else None
    mail_users = Mail.objects.all()
    if user:
        if email not in [i.mail for i in mail_users]:
            Mail.objects.create(mail=email, user=user)
            messages.success(request, 'Ваша почта успешно сохранена')
        else:
            messages.warning(request, 'Ваша почта уже имеется')
    else:
        messages.warning(request, 'Войдите или Зарегистрируйтесь')
        return redirect('login_registration')

    next_page = request.META.get('HTTP_REFERER', 'product_list')
    return redirect(next_page)




def send_mail_to_customer(request):
    superuser = request.user if request.user.is_superuser else None
    if superuser:
        if request.method == 'POST':
            text = request.POST.get('text')
            mail_list = Mail.objects.all()  # получаем все почты из базы
            for email in mail_list:
                mail = send_mail(
                    subject='У нас для вас важная ность',
                    message=text,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False
                )
                print(f'Сообщение отправленно на почту {email} ? - {bool(mail)}')
        else:
            pass
    else:
        return redirect('product_list')

    return render(request, 'store/send_mail.html')



def cart(request):
    if request.user.is_authenticated:
        cart_info = get_cart_data(request)
        context = {
            'cart_total_quantity': cart_info['cart_total_quantity'],
            'order': cart_info['order'],
            'products': cart_info['products']
        }
        return render(request, 'store/cart.html', context)
    else:
        messages.warning(request, 'Авторизутесь или Зарегистрируйтесь')
        return redirect('login_registration')


def to_cart(request, product_id, action):

    if request.user.is_authenticated:
        user_cart = CartForAuthenticatedUser(request, product_id, action)
        next_page = request.META.get('HTTP_REFERER', 'product_list')
        if action == 'add':
            messages.success(request, 'Продукт добавлен в корзину')
        else:
            messages.warning(request, 'Продукт удалён из корзины')
        return redirect(next_page)
    else:
        messages.warning(request, 'Авторизуйтесь или Зарегистрируйтесь')
        return redirect('login_registration')


def checkout(request):
    cart_info = get_cart_data(request)

    context = {
        'cart_total_quantity': cart_info['cart_total_quantity'],
        'order': cart_info['order'],
        'items': cart_info['products'],

        'customer_form': CustomerForm(),
        'shipping_form': ShippingForm(),
        'title': 'Оформление заказа'
    }

    return render(request, 'store/checkout.html', context)


def clear_cart(request):
    user_cart = CartForAuthenticatedUser(request)
    order = user_cart.get_cart_info()['order']
    order_products = order.orderproduct_set.all()  # Получаем все продукты корзины
    for order_product in order_products:  # Проходимся циклом по каждому продукту корзины
        quantity = order_product.quantity  # Получаю кол-во продукта корзины
        product = order_product.product  # Получаю сам продукт корзины
        order_product.delete()  # Удаляю всё из корзины
        product.quantity += quantity  # Возвращаю кол0во каждого продукта на склад
        product.save() # Сохраняю
    messages.error(request, 'Корзина очищенна')
    return redirect('cart')



def create_checkout_session(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if request.method == 'POST':
        user_cart = CartForAuthenticatedUser(request)  # Рождается класс Корзины
        cart_info = user_cart.get_cart_info()  #  Получаем метод класса что бы получить данные о корзине

        customer_form = CustomerForm(data=request.POST)
        if customer_form.is_valid():
            customer = Customer.objects.get(user=request.user)
            customer.first_name = customer_form.cleaned_data['first_name']
            customer.last_name = customer_form.cleaned_data['last_name']
            customer.save()
            user = User.objects.get(username=request.user.username)
            user.first_name = customer_form.cleaned_data['first_name']
            user.last_name = customer_form.cleaned_data['last_name']
            user.save()

        shipping_form = ShippingForm(data=request.POST)
        if shipping_form.is_valid():
            address = shipping_form.save(commit=False)
            address.customer = Customer.objects.get(user=request.user)
            address.order = user_cart.get_cart_info()['order']
            address.save()


        total_price = cart_info['cart_total_price']
        print(total_price)
        total_quantity = cart_info['cart_total_quantity']
        print(total_quantity)
        session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data':{
                        'name': 'товары с TOTEMBO'
                    },
                    'unit_amount': int(total_price * 100)
                },
                'quantity': 1
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('success')),
            cancel_url=request.build_absolute_uri(reverse('success'))
        )
        return redirect(session.url, 303)


def success_payment(request):
    user_cart = CartForAuthenticatedUser(request)
    user_cart.clear()

    messages.success(request, 'Оплата прошла успешно')
    return render(request, 'store/success.html')















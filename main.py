import psycopg2
from psycopg2 import Error
import random
import string
from faker import Faker
from datetime import datetime, timedelta
import uuid

fake_ru = Faker('ru_RU')
fake_en = Faker('en_US')

AMOUNT_USERS = 12000 
AMOUNT_SHOPS = 1000
AMOUNT_PRODUCTS = 8000
AMOUNT_CATEGORIES = 150

def escape_string(s):
    return s.replace("'", "''")

def fill_users():
    query = 'INSERT INTO users(login, pass, mail, phone, address, balance) VALUES '
    existing_logins = set()
    existing_emails = set()
    existing_phones = set()

    values_list = []

    for _ in range(AMOUNT_USERS):
        while True:
            login = fake_ru.user_name()[:20]
            if login not in existing_logins:
                existing_logins.add(login)
                break
        while True:
            email = fake_ru.email()
            if email not in existing_emails:
                existing_emails.add(email)
                break
        while True:
            phone = fake_ru.phone_number()[:20]
            if phone not in existing_phones:
                existing_phones.add(phone)
                break
        password = fake_ru.password(length=random.randint(10, 20))[:50]
        address = fake_ru.address().replace('\n', ', ')
        balance = round(random.uniform(0, 10000), 2)

        login = escape_string(login)
        password = escape_string(password)
        email = escape_string(email)
        phone = escape_string(phone)
        address = escape_string(address)

        values = f"('{login}', '{password}', '{email}', '{phone}', '{address}', {balance})"
        values_list.append(values)

    query += ', '.join(values_list) + ' RETURNING user_id;'
    return query

def fill_categories():
    category_names = set()
    while len(category_names) < AMOUNT_CATEGORIES:
        category_names.add(fake_ru.word().capitalize())

    values_list = []
    for category in category_names:
        category = escape_string(category)
        values = f"('{category}')"
        values_list.append(values)

    query = 'INSERT INTO category(name) VALUES ' + ', '.join(values_list) + ' RETURNING category_id;'
    return query

def fill_shops():
    values_list = []
    for _ in range(AMOUNT_SHOPS):
        min_price = random.choice(range(500, 1600, 100))
        open_hour = random.randint(6, 10)
        close_hour = random.randint(18, 23)
        work_time = f"{open_hour}:00-{close_hour}:00"
        delivery_time = f"{random.randint(30, 120)} мин"

        work_time = escape_string(work_time)
        delivery_time = escape_string(delivery_time)

        values = f"({min_price}, '{work_time}', '{delivery_time}')"
        values_list.append(values)

    query = 'INSERT INTO shop(min_price, work_time, delivery_time) VALUES ' + ', '.join(values_list) + ' RETURNING shop_id;'
    return query

def fill_products():
    product_names = set()
    while len(product_names) < AMOUNT_PRODUCTS:
        word = fake_ru.word().capitalize()
        word2 = fake_ru.word().capitalize()
        product_name = f"{word} {word2}"
        product_names.add(product_name)

    values_list = []
    product_prices = {}
    for product in product_names:
        photo_name = str(uuid.uuid4())
        photo = f'/images/{photo_name}.jpg'
        composition = ' '.join(fake_ru.words(nb=10))
        weight = round(random.uniform(0.1, 10.0), 2)
        rating = 0.0
        price = round(random.uniform(1.0, 500.0), 2)
        protein = round(random.uniform(0.0, 100.0), 2)
        fat = round(random.uniform(0.0, 100.0), 2)
        carbs = round(random.uniform(0.0, 100.0), 2)
        nut_value = f'Б: {protein}, Ж: {fat}, У: {carbs}'

        product = escape_string(product)
        photo = escape_string(photo)
        composition = escape_string(composition)
        nut_value = escape_string(nut_value)

        values = f"('{product}', '{photo}', '{composition}', {weight}, {rating}, {price}, '{nut_value}')"
        values_list.append(values)
        product_prices[product] = price

    query = 'INSERT INTO product(name, photo, composition, weight, rating, price, nut_value) VALUES ' + ', '.join(values_list) + ' RETURNING product_id, name, price;'
    return query, product_prices

def fill_payment_methods(user_ids):
    values_list = []
    for user_id in user_ids:
        num_methods = random.randint(0, 3)
        for _ in range(num_methods):
            cvv = ''.join(random.choice(string.digits) for _ in range(3))
            name = fake_ru.name()[:100]
            bank_name = fake_ru.company()[:100]
            card_num = ''.join(random.choice(string.digits) for _ in range(16))
            exp_date_str = fake_ru.credit_card_expire(start="now", end="+5y", date_format="%Y-%m-%d")
            exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d").date()

            name = escape_string(name)
            bank_name = escape_string(bank_name)

            values = f"({user_id}, '{cvv}', '{name}', '{bank_name}', '{card_num}', '{exp_date}')"
            values_list.append(values)

    if values_list:
        query = 'INSERT INTO payment_method(user_id, cvv, name, bank_name, card_num, exp_date) VALUES ' + ', '.join(values_list) + ';'
    else:
        query = ''
    return query

def fill_favourites(user_ids, product_ids):
    values_list = []
    for user_id in user_ids:
        if random.random() < 0.7:  # 70% вероятность, что пользователь имеет любимые продукты
            max_num_products = min(5, len(product_ids))
            num_favourites = random.randint(1, max_num_products)
            fav_products = random.sample(product_ids, num_favourites)
            for product_id in fav_products:
                values_list.append(f"({user_id}, {product_id})")

    if values_list:
        query = 'INSERT INTO favourites(user_id, product_id) VALUES ' + ', '.join(values_list) + ';'
    else:
        query = ''
    return query

def fill_product_has_category(product_ids, category_ids):
    values_list = []
    for product_id in product_ids:
        max_num_categories = random.randint(1, 3)
        num_categories = random.randint(1, max_num_categories)
        categories = random.sample(category_ids, num_categories)
        for category_id in categories:
            values_list.append(f"({product_id}, {category_id})")

    if values_list:
        query = 'INSERT INTO product_has_category(product_id, category_id) VALUES ' + ', '.join(values_list) + ';'
    else:
        query = ''
    return query

def fill_product_in_shops(product_ids, shop_ids):
    values_list = []
    for product_id in product_ids:
        if random.random() < 0.9:  # 90% вероятность, что продукт есть в магазинах
            max_num_shops = min(5, len(shop_ids))
            num_shops = random.randint(1, max_num_shops)
            shops = random.sample(shop_ids, num_shops)
            for shop_id in shops:
                values_list.append(f"({product_id}, {shop_id})")
        else:
            continue  

    if values_list:
        query = 'INSERT INTO product_in_shops(product_id, shop_id) VALUES ' + ', '.join(values_list) + ';'
    else:
        query = ''
    return query

def fill_cart(user_ids):
    values_list = []
    for user_id in user_ids:
        values_list.append(f"({user_id}, 0.0)")

    query = 'INSERT INTO cart(user_id, price) VALUES ' + ', '.join(values_list) + ' RETURNING cart_id;'
    return query

def fill_cart_contains_product(cart_ids, product_id_to_price):
    values_list = []
    cart_prices = {}

    for cart_id in cart_ids:
        if random.random() < 0.7:  # 70% вероятность, что корзина не пустая
            max_num_products = min(5, len(product_id_to_price))
            num_products = random.randint(1, max_num_products)
            products = random.sample(list(product_id_to_price.keys()), num_products)
            total_price = 0.0
            for product_id in products:
                values_list.append(f"({cart_id}, {product_id})")
                total_price += float(product_id_to_price[product_id])
            total_price = round(total_price, 2)
            cart_prices[cart_id] = total_price
        else:
            cart_prices[cart_id] = 0.0

    if values_list:
        query_insert = 'INSERT INTO cart_contains_product(cart_id, product_id) VALUES ' + ', '.join(values_list) + ';'
    else:
        query_insert = ''

    # Обновляем цены в корзинах
    update_statements = []
    for cart_id, price in cart_prices.items():
        update_statements.append(f"UPDATE cart SET price = {price} WHERE cart_id = {cart_id};")
    update_query = '\n'.join(update_statements)

    return query_insert, update_query

def fill_discount(user_ids):
    values_list = []
    for user_id in user_ids:
        if random.random() < 0.05:  # 5% вероятность, что пользователь имеет скидку
            discount_percentage = random.choice(range(5, 95, 5))
            exp_time = datetime.now() + timedelta(days=random.randint(1, 365))
            values_list.append(f"({user_id}, {discount_percentage}, '{exp_time}')")
    if values_list:
        query = 'INSERT INTO discount(user_id, discount_percentage, exp_time) VALUES ' + ', '.join(values_list) + ';'
    else:
        query = ''
    return query

def fill_orders(user_ids, product_id_to_price):
    data_orders = []
    data_order_products = []
    # Получаем список продуктов, доступных в магазинах
    cursor.execute("SELECT DISTINCT product_id FROM product_in_shops;")
    available_product_ids = [row[0] for row in cursor.fetchall()]
    if not available_product_ids:
        print("Нет доступных продуктов в магазинах для создания заказов.")
        return
    for user_id in user_ids:
        cursor.execute("SELECT pay_method_id FROM payment_method WHERE user_id = %s;", (user_id,))
        users_pay_methods = [row[0] for row in cursor.fetchall()]
        if not users_pay_methods:
            continue
        # Проверяем наличие скидки у пользователя
        cursor.execute("SELECT discount_id, discount_percentage FROM discount WHERE user_id = %s;", (user_id,))
        user_discounts = cursor.fetchall()
        has_discount = len(user_discounts) > 0
        num_orders = random.randint(1, 5)
        for _ in range(num_orders):
            pay_method_id = random.choice(users_pay_methods)
            date = fake_ru.date_between(start_date='-1y', end_date='today')
            time = fake_ru.time()

            max_num_products = min(5, len(available_product_ids))
            num_products = random.randint(1, max_num_products)
            products = random.sample(available_product_ids, num_products)
            total_price = sum(product_id_to_price[pid] for pid in products)
            total_price = round(total_price, 2)
            discount_applied = False
            if has_discount and random.random() < 0.9:  # 90% шанс применения скидки
                discount_applied = True
                discount_id, discount_percentage = user_discounts[0]
                discount_percentage = float(discount_percentage) 
                discount_amount = total_price * (discount_percentage / 100)
                total_price = round(total_price - discount_amount, 2)
                # Удаляем скидку из таблицы discount
                cursor.execute("DELETE FROM discount WHERE discount_id = %s;", (discount_id,))
                connection.commit()
                user_discounts.pop(0)
                has_discount = len(user_discounts) > 0

            data_orders.append({
                'user_id': user_id,
                'pay_method_id': pay_method_id,
                'date': date,
                'time': time,
                'total_price': total_price,
                'discount_applied': discount_applied,
                'products': products
            })
    if data_orders:
        values_list = []
        for order in data_orders:
            values = f"({order['user_id']}, {order['pay_method_id']}, '{order['date']}', '{order['time']}', {order['total_price']}, {order['discount_applied']})"
            values_list.append(values)
        query_orders = 'INSERT INTO orders(user_id, pay_method_id, date, time, total_price, discount_applied) VALUES ' + ', '.join(values_list) + ' RETURNING order_id;'
        cursor.execute(query_orders)
        fetched_order_ids = [row[0] for row in cursor.fetchall()]
        connection.commit()
        idx_order = 0
        for order in data_orders:
            order_id = fetched_order_ids[idx_order]
            for product_id in order['products']:
                data_order_products.append(f"({order_id}, {product_id})")
            idx_order += 1
        if data_order_products:
            query_order_products = 'INSERT INTO order_contains_product(order_id, product_id) VALUES ' + ', '.join(data_order_products) + ';'
            cursor.execute(query_order_products)
            connection.commit()
        print(f"Таблица 'orders' заполнена {len(fetched_order_ids)} записями.")
    else:
        print("Нет данных для вставки в таблицу 'orders'.")

def fill_review():
    data = []
    cursor.execute("SELECT user_id FROM users;")
    user_ids = [row[0] for row in cursor.fetchall()]

    for user_id in user_ids:
        # С вероятностью 30% пользователь пишет отзывы
        if random.random() < 0.3:
            cursor.execute("""
                SELECT DISTINCT product_id FROM order_contains_product 
                WHERE order_id IN (
                    SELECT order_id FROM orders WHERE user_id = %s
                );
            """, (user_id,))
            purchased_products = [row[0] for row in cursor.fetchall()]
            if not purchased_products:
                continue

            # Пользователь может написать отзывы на 1-5 продуктов из купленных
            num_reviews = random.randint(1, min(5, len(purchased_products)))
            for product_id in random.sample(purchased_products, num_reviews):
                cursor.execute("SELECT shop_id FROM product_in_shops WHERE product_id = %s;", (product_id,))
                shops_with_product = [row[0] for row in cursor.fetchall()]
                if not shops_with_product:
                    continue
                shop_id = random.choice(shops_with_product)
                text = fake_ru.paragraph(nb_sentences=3)
                date = fake_ru.date_between(start_date='-1y', end_date='today')
                time = fake_ru.time()
                grade = random.randint(1, 5)

                text = escape_string(text)

                data.append(f"({user_id}, {shop_id}, {product_id}, '{text}', '{date}', '{time}', {grade})")
        else:
            continue  # Пользователь не пишет отзывы

    if data:
        query = 'INSERT INTO review(user_id, shop_id, product_id, text, date, time, grade) VALUES ' + ', '.join(data) + ';'
        cursor.execute(query)
        connection.commit()
        print(f"Таблица 'review' заполнена {len(data)} записями.")
    else:
        print("Нет данных для вставки в таблицу 'review'.")

def fill_coupon():
    data = []
    cursor.execute("SELECT user_id FROM users;")
    user_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT category_id FROM category;")
    category_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT shop_id FROM shop;")
    shop_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT product_id FROM product;")
    product_ids = [row[0] for row in cursor.fetchall()]

    for user_id in user_ids:
        if random.random() < 0.05:  # 5% вероятность, что пользователь имеет купоны
            num_coupons = random.randint(1, 5)
            for _ in range(num_coupons):
                category_id = random.choice(category_ids)
                cursor.execute("SELECT product_id FROM product_has_category WHERE category_id = %s;", (category_id,))
                products_in_category = [row[0] for row in cursor.fetchall()]
                if not products_in_category:
                    continue
                product_id = random.choice(products_in_category)
                cursor.execute("SELECT shop_id FROM product_in_shops WHERE product_id = %s;", (product_id,))
                shops_with_product = [row[0] for row in cursor.fetchall()]
                if not shops_with_product:
                    continue
                shop_id = random.choice(shops_with_product)
                discount_amount = random.choice(range(100, 3100, 100))
                data.append(f"({user_id}, {category_id}, {shop_id}, {product_id}, {discount_amount})")

    if data:
        query = 'INSERT INTO coupon(user_id, category_id, shop_id, product_id, discount_amount) VALUES ' + ', '.join(data) + ';'
        cursor.execute(query)
        connection.commit()
        print(f"Таблица 'coupon' заполнена {len(data)} записями.")
    else:
        print("Нет данных для вставки в таблицу 'coupon'.")

try:
    connection = psycopg2.connect(user="postgres",
                                  password="root",
                                  host="localhost",
                                  port="5432",
                                  database="sbermarket2")

    cursor = connection.cursor()

    print("Информация о сервере PostgreSQL")
    print(connection.get_dsn_parameters(), "\n")

    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print("Вы подключены к - ", record, "\n")

    # Заполнение таблиц
    cursor.execute(fill_users())
    user_ids = [row[0] for row in cursor.fetchall()]
    connection.commit()
    print(f"Таблица 'users' заполнена {len(user_ids)} записями.")

    cursor.execute(fill_categories())
    category_ids = [row[0] for row in cursor.fetchall()]
    connection.commit()
    print(f"Таблица 'category' заполнена {len(category_ids)} записями.")

    cursor.execute(fill_shops())
    shop_ids = [row[0] for row in cursor.fetchall()]
    connection.commit()
    print(f"Таблица 'shop' заполнена {len(shop_ids)} записями.")

    query, product_prices = fill_products()
    cursor.execute(query)
    results = cursor.fetchall()
    product_ids = []
    product_id_to_price = {}
    for row in results:
        product_id = row[0]
        name = row[1]
        price = float(row[2])
        product_ids.append(product_id)
        product_id_to_price[product_id] = price
    connection.commit()
    print(f"Таблица 'product' заполнена {len(product_ids)} записями.")

    query = fill_payment_methods(user_ids)
    if query:
        cursor.execute(query)
        connection.commit()
        print("Таблица 'payment_method' заполнена.")

    query = fill_favourites(user_ids, product_ids)
    if query:
        cursor.execute(query)
        connection.commit()
        print("Таблица 'favourites' заполнена.")

    query = fill_product_has_category(product_ids, category_ids)
    if query:
        cursor.execute(query)
        connection.commit()
        print("Таблица 'product_has_category' заполнена.")

    query = fill_product_in_shops(product_ids, shop_ids)
    if query:
        cursor.execute(query)
        connection.commit()
        print("Таблица 'product_in_shops' заполнена.")

    cursor.execute(fill_cart(user_ids))
    cart_ids = [row[0] for row in cursor.fetchall()]
    connection.commit()
    print(f"Таблица 'cart' заполнена {len(cart_ids)} записями.")

    query_insert, update_query = fill_cart_contains_product(cart_ids, product_id_to_price)
    if query_insert:
        cursor.execute(query_insert)
        connection.commit()
        print("Таблица 'cart_contains_product' заполнена.")
    if update_query:
        cursor.execute(update_query)
        connection.commit()
        print("Цены в корзинах обновлены.")

    query = fill_discount(user_ids)
    if query:
        cursor.execute(query)
        connection.commit()
        print("Таблица 'discount' заполнена.")

    fill_orders(user_ids, product_id_to_price)
    fill_review()

    update_product_ratings_query = '''
    UPDATE product SET rating = sub.avg_grade
    FROM (
        SELECT product_id, ROUND(AVG(grade)::numeric, 2) as avg_grade
        FROM review
        GROUP BY product_id
    ) sub
    WHERE product.product_id = sub.product_id;
    '''
    cursor.execute(update_product_ratings_query)
    connection.commit()
    print("Рейтинг продуктов обновлен на основе отзывов.")

    fill_coupon()

except (Exception, Error) as error:
    print("Ошибка при работе с PostgreSQL:", error)
finally:
    if connection:
        cursor.close()
        connection.close()
        print("Соединение с PostgreSQL закрыто")

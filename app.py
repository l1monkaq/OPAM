from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- КЛАСИ ОБ'ЄКТНОЇ МОДЕЛІ (ООП / ОПАМ) ---

class BaseService:
    """Базовий клас для всіх послуг шиномонтажу (Спадкування)."""
    def __init__(self, service_id, name):
        self.service_id = service_id
        self.name = name

    def get_price(self, car_type, radius):
        """Абстрактний метод, який кожен підклас реалізує по-своєму (Поліморфізм)."""
        raise NotImplementedError("Субкласи мають реалізувати цей метод")


class FixedPriceService(BaseService):
    """Послуги з фіксованою ціною (не залежать від радіуса чи типу авто)."""
    def __init__(self, service_id, name, price):
        super().__init__(service_id, name)
        self.price = price

    def get_price(self, car_type, radius):
        return self.price


class ComplexPriceService(BaseService):
    """Послуги, ціна яких залежить від типу авто та діапазону радіуса коліс."""
    def __init__(self, service_id, name, price_matrix):
        super().__init__(service_id, name)
        self.price_matrix = price_matrix

    def get_price(self, car_type, radius):
        try:
            # Визначаємо, в який діапазон з прайсу тата потрапляє вибраний радіус
            if radius in [13, 14]:
                r_range = "R13-14"
            elif radius in [15, 16]:
                r_range = "R15-16"
            elif radius in [17, 18]:
                r_range = "R17-18"
            elif radius in [19, 20]:
                r_range = "R19-20"
            else:
                # На випадок R21 та R22 беремо максимальну ціну з прайсу
                r_range = "R19-20" 

            return self.price_matrix[car_type][r_range]
        except KeyError:
            return 0


class Order:
    """Клас замовлення, що інкапсулює логіку вибору та підрахунку (Інкапсуляція)."""
    def __init__(self, car_type, radius, quantity=4):
        self.car_type = car_type          # 'passenger' або 'suv'
        self.radius = int(radius)         # Число (13, 14, 15...)
        self.quantity = quantity          # Кількість коліс
        self.selected_services = []

    def add_service(self, service):
        self.selected_services.append(service)

    def calculate_total(self):
        """Рахує повну вартість замовлення."""
        total = 0
        for service in self.selected_services:
            # Якщо послуга комплексна — множимо на кількість коліс, якщо фіксована — додаємо один раз
            if isinstance(service, ComplexPriceService):
                total += service.get_price(self.car_type, self.radius) * self.quantity
            else:
                total += service.get_price(self.car_type, self.radius)
        return total


# --- РЕАЛЬНІ ДАНІ З ТАТОВОГО ПРАЙСУ ---
# Взято ціни для Литих (Л) дисків, оскільки вони найпопулярніші
complex_pricing = {
    "passenger": {
        "R13-14": 275,  # Ціна за 1 колесо (Зняти + Шино-ж + Баланс)
        "R15-16": 300,
        "R17-18": 335,
        "R19-20": 375
    },
    "suv": {
        "R13-14": 340,
        "R15-16": 340,  
        "R17-18": 375,
        "R19-20": 425
    }
}

# Створюємо каталог об'єктів-послуг (демонстрація Поліморфізму в масиві)
services_catalog = [
    ComplexPriceService("full_complex", "Комплекс (Монтаж + Демонтаж + Баланс)", complex_pricing),
    FixedPriceService("repair_puncture", "Ремонт проколу (латка) / жгут", 150),
    FixedPriceService("valve_replace", "Заміна вентиля (клапана)", 40),
    FixedPriceService("wheel_cleaning", "Чистка борту диска герметиком", 50)
]


# --- ВЕБ-МАРШРУТИ (FLASK ROUTES) ---

@app.route('/')
def index():
    # Передаємо список послуг на фронтенд для динамічного відображення
    return render_template('index.html', services=services_catalog)


@app.route('/calculate', methods=['POST'])
def calculate():
    # Отримуємо JSON-дані від вебсторінки
    data = request.json
    car_type = data.get('car_type')
    radius = data.get('radius')
    chosen_service_ids = data.get('services', [])
    quantity = int(data.get('quantity', 4))

    # Створюємо об'єкт замовлення (ООП у дії)
    order = Order(car_type, radius, quantity)

    # Шукаємо вибрані послуги в каталозі та додаємо до замовлення
    for s_id in chosen_service_ids:
        service_obj = next((s for s in services_catalog if s.service_id == s_id), None)
        if service_obj:
            order.add_service(service_obj)

    # Рахуємо фінальну суму через об'єкт
    total_price = order.calculate_total()
    
    return jsonify({"total": total_price})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
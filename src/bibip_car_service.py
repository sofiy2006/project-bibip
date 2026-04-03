import os
from decimal import Decimal
from datetime import datetime
from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path

    def _car_to_string(self, car: Car) -> str:
        parts = [
            car.vin,
            str(car.model),
            str(car.price),
            car.date_start.isoformat(),
            car.status.value
        ]
        return "|".join(parts)

    def _string_to_car(self, line: str) -> Car:
        parts = line.strip().split('|')
        return Car(
            vin=parts[0],
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus(parts[4])
        )

    def _model_to_string(self, model: Model) -> str:
        return f"{model.id}|{model.name}|{model.brand}"

    def _string_to_model(self, line: str) -> Model:
        parts = line.strip().split('|')
        return Model(
            id=int(parts[0]),
            name=parts[1],
            brand=parts[2]
        )

    def _sale_to_string(self, sale: Sale) -> str:
        return f"{sale.sales_number}|{sale.car_vin}|{sale.sales_date.isoformat()}|{sale.cost}"

    def _string_to_sale(self, line: str) -> Sale:
        parts = line.strip().split('|')
        return Sale(
            sales_number=parts[0],
            car_vin=parts[1],
            sales_date=datetime.fromisoformat(parts[2]),
            cost=Decimal(parts[3])
        )

    def _get_next_line_number(self, filename: str) -> int:
        if not os.path.exists(filename):
            return 0
        
        with open(filename, 'r') as f:
            return sum(1 for _ in f)

    def _write_line_to_file(self, filename: str, line_number: int, data: str):
        formatted_line = data.ljust(500) + '\n'
        position = line_number * 501
        
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                pass
        
        with open(filename, 'r+') as f:
            f.seek(position)
            f.write(formatted_line)

    def _read_line_from_file(self, filename: str, line_number: int) -> str:
        if not os.path.exists(filename):
            return ""
        
        position = line_number * 501
        
        with open(filename, 'r') as f:
            f.seek(position)
            line = f.read(500)
            return line.rstrip()

    def _add_to_index(self, index_filename: str, key: str, line_number: int):
        with open(index_filename, 'a') as f:
            f.write(f"{key}|{line_number}\n")

    def _get_from_index(self, index_filename: str, key: str) -> int | None:
        if not os.path.exists(index_filename):
            return None
        
        with open(index_filename, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) == 2:
                    k, line_num = parts
                    if k == key:
                        return int(line_num)
        return None

    def _remove_from_index(self, index_filename: str, key: str):
        if not os.path.exists(index_filename):
            return
        
        with open(index_filename, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            parts = line.strip().split('|')
            if len(parts) == 2 and parts[0] != key:
                new_lines.append(line)
        
        with open(index_filename, 'w') as f:
            f.writelines(new_lines)

    def _get_car_by_vin(self, vin: str) -> Car | None:
        cars_index_file = os.path.join(self.root_directory_path, "index_cars.txt")
        cars_file = os.path.join(self.root_directory_path, "cars.txt")
        
        line_number = self._get_from_index(cars_index_file, vin)
        if line_number is None:
            return None
        
        car_str = self._read_line_from_file(cars_file, line_number)
        if not car_str:
            return None
        
        return self._string_to_car(car_str)

    def _update_car(self, car: Car) -> None:
        """Обновляет существующую машину в файле"""
        cars_index_file = os.path.join(self.root_directory_path, "index_cars.txt")
        cars_file = os.path.join(self.root_directory_path, "cars.txt")
        
        line_number = self._get_from_index(cars_index_file, car.vin)
        if line_number is not None:
            car_str = self._car_to_string(car)
            self._write_line_to_file(cars_file, line_number, car_str)

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        models_file = os.path.join(self.root_directory_path, "models.txt")
        index_file = os.path.join(self.root_directory_path, "index_models.txt")
        
        os.makedirs(self.root_directory_path, exist_ok=True)
        
        line_number = self._get_next_line_number(models_file)
        data_str = self._model_to_string(model)
        
        self._write_line_to_file(models_file, line_number, data_str)
        self._add_to_index(index_file, model.index(), line_number)
        
        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        cars_file = os.path.join(self.root_directory_path, "cars.txt")
        index_file = os.path.join(self.root_directory_path, "index_cars.txt")
        
        os.makedirs(self.root_directory_path, exist_ok=True)
        
        line_number = self._get_next_line_number(cars_file)
        data_str = self._car_to_string(car)
        
        self._write_line_to_file(cars_file, line_number, data_str)
        self._add_to_index(index_file, car.index(), line_number)

        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        car = self._get_car_by_vin(sale.car_vin)
        if car is None:
            raise Exception(f"Car {sale.car_vin} not found")

        if car.status == CarStatus.sold:
            raise Exception(f"Car {sale.car_vin} is already sold")
        
        if car.status == CarStatus.delivery:
            raise Exception(f"Car {sale.car_vin} is not available for sale")

        sales_file = os.path.join(self.root_directory_path, "sales.txt")
        index_sales_file = os.path.join(self.root_directory_path, "index_sales.txt")
        
        os.makedirs(self.root_directory_path, exist_ok=True)
        
        line_number = self._get_next_line_number(sales_file)
        sale_str = self._sale_to_string(sale)
        
        self._write_line_to_file(sales_file, line_number, sale_str)
        self._add_to_index(index_sales_file, sale.car_vin, line_number)

        car.status = CarStatus.sold
        self._update_car(car)
        
        return car

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        cars_file = os.path.join(self.root_directory_path, "cars.txt")
        result = []
        
        if not os.path.exists(cars_file):
            return result
        
        line_number = 0
        while True:
            car_str = self._read_line_from_file(cars_file, line_number)
            if not car_str:
                break
            
            car = self._string_to_car(car_str)
            if car.status == status:
                result.append(car)
            
            line_number += 1
        
        return result

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        car = self._get_car_by_vin(vin)
        if car is None:
            return None

        models_index_file = os.path.join(self.root_directory_path, "index_models.txt")
        models_file = os.path.join(self.root_directory_path, "models.txt")
        
        model_line = self._get_from_index(models_index_file, str(car.model))
        if model_line is None:
            return None
        
        model_str = self._read_line_from_file(models_file, model_line)
        model_parts = model_str.split('|')
        model_name = model_parts[1]
        model_brand = model_parts[2]

        sales_index_file = os.path.join(self.root_directory_path, "index_sales.txt")
        sales_file = os.path.join(self.root_directory_path, "sales.txt")
        
        sale_line = self._get_from_index(sales_index_file, vin)
        sale_date = None
        sale_cost = None
        
        if sale_line is not None:
            sale_str = self._read_line_from_file(sales_file, sale_line)
            sale_parts = sale_str.split('|')
            sale_date = datetime.fromisoformat(sale_parts[2])
            sale_cost = Decimal(sale_parts[3])
        
        return CarFullInfo(
            vin=car.vin,
            car_model_name=model_name,
            car_model_brand=model_brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=sale_date,
            sales_cost=sale_cost
        )

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        old_car = self._get_car_by_vin(vin)
        if old_car is None:
            raise Exception(f"Car {vin} not found")

        new_car = Car(
            vin=new_vin,
            model=old_car.model,
            price=old_car.price,
            date_start=old_car.date_start,
            status=old_car.status
        )

        self.add_car(new_car)

        cars_index_file = os.path.join(self.root_directory_path, "index_cars.txt")
        self._remove_from_index(cars_index_file, vin)

        sales_index_file = os.path.join(self.root_directory_path, "index_sales.txt")
        sales_file = os.path.join(self.root_directory_path, "sales.txt")
        
        sale_line = self._get_from_index(sales_index_file, vin)
        if sale_line is not None:
            sale_str = self._read_line_from_file(sales_file, sale_line)
            sale_parts = sale_str.split('|')

            new_sale_str = f"{sale_parts[0]}|{new_vin}|{sale_parts[2]}|{sale_parts[3]}"
            self._write_line_to_file(sales_file, sale_line, new_sale_str)

            self._remove_from_index(sales_index_file, vin)
            self._add_to_index(sales_index_file, new_vin, sale_line)
        
        return new_car

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        sales_file = os.path.join(self.root_directory_path, "sales.txt")
        
        if not os.path.exists(sales_file):
            raise Exception("No sales found")

        found_vin = None
        found_line = None
        
        line_number = 0
        while True:
            sale_str = self._read_line_from_file(sales_file, line_number)
            if not sale_str:
                break
            
            parts = sale_str.split('|')
            if len(parts) >= 1 and parts[0] == sales_number:
                found_vin = parts[1]
                found_line = line_number
                break
            
            line_number += 1
        
        if found_vin is None:
            raise Exception(f"Sale {sales_number} not found")

        sales_index_file = os.path.join(self.root_directory_path, "index_sales.txt")
        self._remove_from_index(sales_index_file, found_vin)

        car = self._get_car_by_vin(found_vin)
        if car is None:
            raise Exception(f"Car {found_vin} not found")
        
        car.status = CarStatus.available
        self._update_car(car)
        
        return car

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        sales_file = os.path.join(self.root_directory_path, "sales.txt")
        
        if not os.path.exists(sales_file):
            return []

        sales_count = {}
        
        line_number = 0
        while True:
            sale_str = self._read_line_from_file(sales_file, line_number)
            if not sale_str:
                break
            
            parts = sale_str.split('|')
            if len(parts) >= 2:
                car_vin = parts[1]
                car = self._get_car_by_vin(car_vin)
                if car:
                    model_id = car.model
                    sales_count[model_id] = sales_count.get(model_id, 0) + 1
            
            line_number += 1

        models_file = os.path.join(self.root_directory_path, "models.txt")
        models_info = {}
        
        if os.path.exists(models_file):
            line_number = 0
            while True:
                model_str = self._read_line_from_file(models_file, line_number)
                if not model_str:
                    break
                
                parts = model_str.split('|')
                if len(parts) >= 3:
                    model_id = int(parts[0])
                    model_name = parts[1]
                    model_brand = parts[2]
                    models_info[model_id] = (model_name, model_brand)
                
                line_number += 1

        results = []
        for model_id, count in sales_count.items():
            if model_id in models_info:
                name, brand = models_info[model_id]
                results.append(ModelSaleStats(
                    car_model_name=name,
                    brand=brand,
                    sales_number=count
                ))

        results.sort(key=lambda x: x.sales_number, reverse=True)
        return results[:3]
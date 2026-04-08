import pickle
from collections import UserDict
from datetime import datetime, timedelta

# --- Класи полів ---

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        # Валідація телефону: 10 цифр
        if not (len(value) == 10 and value.isdigit()):
            raise ValueError("Телефон має складатися з 10 цифр.")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            # Перевіряємо формат, зберігаємо як рядок згідно з умовою ДЗ 7
            datetime.strptime(value, "%d.%m.%Y")
            self.value = value
        except ValueError:
            raise ValueError("Неправильний формат дати. Використовуйте DD.MM.YYYY")

# --- Класи сутностей ---

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def edit_phone(self, old_phone, new_phone):
        for idx, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[idx] = Phone(new_phone)
                return
        raise ValueError(f"Телефон {old_phone} не знайдено.")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def __str__(self):
        birthday_str = f", день народження: {self.birthday}" if self.birthday else ""
        phones_str = "; ".join(p.value for p in self.phones)
        return f"Контакт: {self.name.value}, телефони: {phones_str}{birthday_str}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def get_upcoming_birthdays(self):
        upcoming = []
        today = datetime.today().date()
        
        for record in self.data.values():
            if not record.birthday:
                continue
            
            # Конвертуємо рядок з Birthday назад у дату для розрахунків
            bday = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
            bday_this_year = bday.replace(year=today.year)
            
            if bday_this_year < today:
                bday_this_year = bday_this_year.replace(year=today.year + 1)
            
            days_until = (bday_this_year - today).days
            
            if 0 <= days_until <= 7:
                congratulation_date = bday_this_year
                # Якщо вихідний — переносимо на понеділок
                if congratulation_date.weekday() == 5:  # Субота
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:  # Неділя
                    congratulation_date += timedelta(days=1)
                
                upcoming.append({
                    "name": record.name.value,
                    "birthday": congratulation_date.strftime("%d.%m.%Y")
                })
        return upcoming

# --- Функції для роботи з файлами (Pickle) ---

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        return AddressBook()

# --- Декоратор та хендлери ---

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Контакт не знайдено."
        except IndexError:
            return "Будь ласка, введіть ім'я та необхідні дані (телефон/дата)."
        except AttributeError:
            return "Контакт не знайдено."
    return inner

def parse_input(user_input):
    if not user_input.strip():
        return "ignore", []
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Контакт оновлено."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Контакт додано."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.data[name]  # Викличе KeyError, якщо немає в базі
    record.edit_phone(old_phone, new_phone)
    return "Телефон змінено."

@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.data[name]
    if not record.phones:
        return f"У контакта {name} немає збережених номерів."
    return f"{name}: {'; '.join(p.value for p in record.phones)}"

@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "Адресна книга порожня."
    return "\n".join(str(record) for record in book.data.values())

@input_error
def add_birthday(args, book: AddressBook):
    name, date = args
    record = book.data[name]
    record.add_birthday(date)
    return "День народження додано."

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.data[name]
    if record.birthday:
        return f"День народження {name}: {record.birthday.value}"
    return f"Для {name} не вказано дату народження."

@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "На найближчий тиждень іменинників немає."
    res = []
    for u in upcoming:
        res.append(f"{u['name']}: {u['birthday']}")
    return "\n".join(res)

# --- Main ---

def main():
    # Завантаження даних при запуску
    book = load_data()
    print("Welcome to the assistant bot!")
    
    while True:
        user_input = input("Enter a command: ").strip()
        if not user_input:
            continue
            
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            # Збереження перед виходом
            save_data(book)
            print("Good bye!")
            break
            
        elif command == "hello":
            print("How can I help you?")
            
        elif command == "add":
            print(add_contact(args, book))
            
        elif command == "change":
            print(change_contact(args, book))
            
        elif command == "phone":
            print(show_phone(args, book))
            
        elif command == "all":
            print(show_all(book))
            
        elif command == "add-birthday":
            print(add_birthday(args, book))
            
        elif command == "show-birthday":
            print(show_birthday(args, book))
            
        elif command == "birthdays":
            print(birthdays(args, book))
            
        elif command == "ignore":
            continue
            
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
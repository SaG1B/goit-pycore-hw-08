import pickle
from collections import UserDict
from datetime import datetime, timedelta

# --- Класи даних (Field, Name, Phone, Birthday, Record, AddressBook) ---
# (Залишаємо без змін з попереднього кроку)

class Field:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not (len(value) == 10 and value.isdigit()):
            raise ValueError("Phone number must be 10 digits.")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
    def __str__(self):
        return self.value.strftime("%d.%m.%Y")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def edit_phone(self, old_number, new_number):
        for i, phone in enumerate(self.phones):
            if phone.value == old_number:
                self.phones[i] = Phone(new_number)
                return
        raise ValueError(f"Phone {old_number} not found.")

    def add_birthday(self, date):
        self.birthday = Birthday(date)

    def __str__(self):
        res = f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"
        if self.birthday:
            res += f", birthday: {self.birthday}"
        return res

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def get_upcoming_birthdays(self):
        upcoming_birthdays = []
        today = datetime.today().date()
        for user in self.data.values():
            if not user.birthday: continue
            bday = user.birthday.value.replace(year=today.year)
            if bday < today: bday = bday.replace(year=today.year + 1)
            if 0 <= (bday - today).days <= 7:
                congrat_date = bday
                if congrat_date.weekday() == 5: congrat_date += timedelta(days=2)
                elif congrat_date.weekday() == 6: congrat_date += timedelta(days=1)
                upcoming_birthdays.append({"name": user.name.value, "birthday": congrat_date.strftime("%d.%m.%Y")})
        return upcoming_birthdays

# --- Функції для роботи з файлами (Pickle) ---

def save_data(book, filename="addressbook.pkl"):
    """Збереження адресної книги у файл."""
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    """Завантаження адресної книги з файлу або створення нової."""
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        return AddressBook()

# --- Декоратор та Хендлери ---

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, IndexError, KeyError) as e:
            return str(e) if str(e) else "Invalid input or contact not found."
    return inner

def parse_input(user_input):
    if not user_input.strip(): return "ignore", []
    cmd, *args = user_input.split()
    return cmd.strip().lower(), *args

@input_error
def add_contact(args, book):
    name, phone = args[0], args[1] if len(args) > 1 else None
    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)
        msg = "Contact added."
    else:
        msg = "Contact updated."
    if phone: record.add_phone(phone)
    return msg

@input_error
def add_birthday(args, book):
    name, date = args
    record = book.find(name)
    if record:
        record.add_birthday(date)
        return "Birthday added."
    raise KeyError

# --- Головний цикл ---

def main():
    # 1. Відновлення даних при запуску
    book = load_data()
    print("Welcome to the assistant bot!")
    
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            # 2. Збереження даних перед виходом
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "all":
            for record in book.data.values():
                print(record)

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "birthdays":
            upcoming = book.get_upcoming_birthdays()
            for entry in upcoming:
                print(f"{entry['name']}: {entry['birthday']}")
        
        elif command == "ignore":
            continue
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
from dataclasses import dataclass

@dataclass
class Being:
    name: str

@dataclass
class Person(Being):
    likesDogs: bool

@dataclass
class Dog(Being):
    weight: float

julia = Person("Julia", True)
oliver = Dog("Ollie", 95.5)

print(julia)         # Person(name='Julia', likesDogs=True)
print(oliver.weight) # 95.5

def greet(being):
    match being:
        case Person(name, True):
            print(f"Hi, {name}!")
        case Person(name, False):
            print(f"Hello, {name}!")
        case Dog(_, weight):
            if weight > 80.0:
                print("Who's a good boy?")
            else:
                print("Hey pup!")
        case _:
            print("...")


greet(julia)  # Hi, Julia!
greet(oliver) # Who's a good boy?
greet("foo")  # ...


import sys
from mandelbrot import animate_mandelbrot
from l_system import animate_koch_snowflake, animate_sierpinski_triangle, animate_dragon_curve

def main():
    print("Выберите фрактал для отображения:")
    print("1. Множество Мандельброта (с анимацией зума)")
    print("2. Снежинка Коха (с анимацией построения)")
    print("3. Треугольник Серпинского (с анимацией построения)")
    print("4. Кривая дракона (с анимацией построения)")
    
    choice = input("Введите номер (1-4): ")
    
    if choice == "1":
        animate_mandelbrot()
    elif choice == "2":
        animate_koch_snowflake()
    elif choice == "3":
        animate_sierpinski_triangle()
    elif choice == "4":
        animate_dragon_curve()
    else:
        print("Неверный выбор. Пожалуйста, выберите число от 1 до 4.")
        sys.exit(1)

if __name__ == "__main__":
    main() 
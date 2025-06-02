# FireStrike - Децентрализованная DHT-сеть

Это реализация децентрализованной хеш-таблицы (DHT) для обмена файлами в распределенной сети. Проект обеспечивает безопасное хранение и поиск данных.

## Особенности

- Прямые P2P соединения через TCP/IP
- Хеширование файлов с использованием SHA-3 и соли
- Асимметричное шифрование для обмена сообщениями
- Автоматическое обнаружение пиров в сети
- Распределенное хранение данных

## Требования

- Python 3.7+
- Зависимости Python из requirements.txt

## Установка

1. Установите зависимости Python:
   ```bash
   pip install -r requirements.txt
   ```

## Использование

1. Запуск узла:
   ```bash
   python -m firestrike --port 8788
   ```

2. Загрузка файла:
   ```bash
   firestrike upload path/to/file
   ```

3. Скачивание файла:
   ```bash
   firestrike download <hash> --output path/to/save
   ```

4. Просмотр подключенных пиров:
   ```bash
   firestrike peers
   ```

## Безопасность

- Все файлы шифруются перед отправкой
- Используется асимметричное шифрование для обмена ключами
- Хеширование файлов с солью для защиты от атак
- Проверка целостности данных

## Настройка портов

По умолчанию узел использует порт 8788. Вы можете изменить его при запуске:
```bash
firestrike --port 8789
```

## Временные файлы

Для хранения временных файлов используется директория `firestrike_temp`. 
Вы можете изменить её расположение с помощью опции `--temp`:
```bash
firestrike --temp /path/to/temp
```

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Submit a pull request

## Warning

This project is intended for legal file sharing. The authors are not responsible for its misuse. 
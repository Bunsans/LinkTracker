# Backend Academy 2025 Python Template

Welcome to the **Backend Academy 2025 Python Template**! This repository serves as a starting point for your Python projects, using **Poetry** for dependency management and packaging.


## TODO

- [x] Бот должен поддерживать следующие команды:
- [x] Команда /list должна выводить специальное сообщение, если список отслеживаемых ссылок пуст.
- [x] Неизвестные команды должны игнорироваться с уведомлением пользователю.
- [x] Все endpoint'ы соответствуют OpenAPI-контракту
- [x] Реализован базовый планировщик: бот присылает простейшее уведомление (заглушку) в случае обнаружения изменений
- [x] Общение между приложениями bot и scrapper происходит по HTTP
- [ ] Добавить паттерн Репозиторий для хранения данных(на данный момент реализован простой dict)
- [ ] Добавить игнорирование неизвестных команд типа /\<command\>.
## TODO нефункциональные
- [x] Токен авторизации должен храниться в конфигурационном файле, недоступном для общего доступа
- [x] Поддерживается скреппинг вопросов StackOverflow и репозиториев GitHub -- вам нужно написать HTTP-клиентов для получения необходимой информации из API
- [x] Не нужно парсить страницу (HTML), нужно работать с API: GitHub, StackOverflow
- [x] Запрещается использовать готовые SDK для доступа к API для HTTP-клиентов (GitHub, StackOverflow):
- [x] Клиентов нужно написать руками
- [x] Бот должен реализовывать концепт машины состояний (создание /track должно идти в формате диалога, а не команды):
- [ ] В тестах запрещено делать реальные вызовы к API внешних систем, нужно использовать заглушки (mocks)
- [x] Используйте типобезопасную конфигурацию
- [ ] Cтруктурное логирование (добавление key-value значений к логу, вместо зашивания данных в поле message) в коде приложения
## TODO tests
- [x] Корректный парсинг ссылок
- [ ] Правильное сохранение данных в репозиторий из запроса пользователя: ссылка, тэги, фильтры
- [ ]  Бот кидает ошибку, если команда неизвестна
- [ ] Тесты на happy path: добавление и удаление ссылок из репозитория
- [ ] Тест на добавление дубля ссылки
- [ ]  Тесты для планировщика: обновление отправляется только пользователям, которые следят за ссылкой
- [ ] Тесты на корректную обработку ошибок HTTP-запросов (некорректное тело, код) в клиентах
- [ ] Проверка форматирования команды /list


## Table of Contents

- [Requirements](#requirements)
- [Setup](#setup)
- [Running the Project](#running-the-project)
- [Testing](#testing)
- [Linting](#linting)
- [Useful Commands](#useful-commands)
- [Contributing](#contributing)
- [License](#license)

## Requirements

To work with this template, you'll need the following installed:

- **Python 3.11+**: Ensure Python is installed and available in your PATH.
- **Poetry**: Dependency management tool for Python. You can install it via:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

## Setup

1. **Install dependencies:**

   ```bash
   make install
   ```

2. **Activate the virtual environment:**

   Poetry automatically creates a virtual environment for your project. To activate it:

   ```bash
   poetry shell
   ```

## Running the Project

To start the application, use the following command:

```bash
bash start.sh
```

In another terminal start server
```bash
bash start_server.sh
```

## Testing

The project includes a basic test suite. To run tests, use:

```bash
make test
```

## Linting

Ensure your code meets the style guidelines:

```bash
make lint
```

## Useful Commands

Here are some commands you might find useful during development:

- **Add a new package:**

  ```bash
  poetry add <package-name>
  ```

- **Add a new development package:**

  ```bash
  poetry add --dev <package-name>
  ```

- **Update dependencies:**

  ```bash
  poetry update
  ```

- **Run the application:**

  ```bash
  poetry run python -m src.main
  ```

- **Run tests:**

  ```bash
  make test
  ```

- **Run linters in format mode, possibly fixing problems:**

  ```bash
  make format
  ```
  
## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

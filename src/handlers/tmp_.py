# Напиши тесты для этих функций бота, используй

# @pytest.fixture(scope="session")
# def mock_event() -> Mock:
#     event = Mock(spec=NewMessage.Event)
#     event.input_chat = "test_chat"
#     event.chat_id = 123456789
#     event.message = "/chat_id"
#     event.client = MagicMock(spec=TelegramClient)
#     return event


# async def chat_id_cmd_handler(
#     event: NewMessage.Event,
# ) -> None:
#     if event.chat_id in user_states:
#         del user_states[event.chat_id]

#     logger.info("Chat ID: %s\n entity: %s", event.chat_id, event.input_chat)
#     await event.client.send_message(
#         entity=event.input_chat,
#         message=f"chat_id is: {event.chat_id}",
#         reply_to=event.message,
#     )


# async def track_cmd_handler(
#     event: NewMessage.Event,
# ) -> None:
#     if not await is_chat_registrated(event):
#         return
#     message = event.message.message
#     args = message.split()
#     user_id = event.chat_id
#     if len(args) > 1:
#         await send_message_from_bot(event, "Введите тэги (опционально):")
#         link = args[1]
#         user_states[user_id] = State(state=STATE_TAGS, link=link)
#     else:

#         await send_message_from_bot(event, "Введите ссылку для отслеживания:")
#         user_states[user_id] = State(state=STATE_TRACK)


# async def unknown_command_handler(event: NewMessage.Event) -> None:
#     await send_message_from_bot(event, "Не знаю такой команды(")


# async def message_handler(event: NewMessage.Event) -> None:
#     logger.debug(f"user_states: {user_states}")
#     user_id = event.chat_id
#     if user_id not in user_states:
#         await send_message_from_bot(event, "Не пон")
#         return

#     current_state = user_states[user_id]

#     if current_state.state == STATE_TRACK:
#         link = event.raw_text
#         user_states[user_id] = State(state=STATE_TAGS, link=link)
#         await send_message_from_bot(event, "Введите тэги (опционально):")

#     elif current_state.state == STATE_TAGS:
#         link = current_state.link
#         tags = event.raw_text.split()
#         user_states[user_id] = State(STATE_FILTERS, link, tags)
#         await send_message_from_bot(event, "Настройте фильтры (опционально):")
#     elif current_state.state == STATE_FILTERS:
#         link, tags = current_state.link, current_state.tags
#         filters = event.raw_text.split()
#         try:
#             body = AddLinkRequest(link=link, tags=tags, filters=filters)
#         except ValueError:
#             await send_message_from_bot(
#                 event,
#                 "Неверный формат для ссылки. Про форматы смотрите в /help",
#             )
#             del user_states[user_id]
#             return
#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 url=api_settings.url_server + "/links",
#                 headers={"tg-chat-id": str(event.chat_id)},
#                 json=body.model_dump(),
#             )
#             match response.status_code:
#                 case status.HTTP_200_OK:
#                     message = f"Ссылка {link} добавлена с тэгами: {tags} и фильтрами: {filters}"
#                 case status.HTTP_401_UNAUTHORIZED:
#                     message = "Чат не зарегистрирован, для регистрации введите /start"
#                 case _:
#                     message = response.text
#             await send_message_from_bot(event, message)

#             del user_states[user_id]


# async def untrack_cmd_handler(
#     event: NewMessage.Event,
# ) -> None:
#     if event.chat_id in user_states:
#         del user_states[event.chat_id]

#     if not await is_chat_registrated(event):
#         return
#     message = event.message.message
#     args = message.split()
#     chat_id = event.chat_id
#     if len(args) == 1:
#         await send_message_from_bot(
#             event,
#             """Пожалуйста, введите ссылку от которой хотите отписаться
# (/untrack <ссылка>)""",
#         )
#         return
#     else:
#         link = args[1]
#         async with httpx.AsyncClient() as client:
#             response = await client.delete(
#                 url=api_settings.url_server + "/links",
#                 headers={"tg-chat-id": str(chat_id)},
#                 params={"link": link},
#             )
#             status_code = response.status_code
#             match status_code:
#                 case status.HTTP_200_OK:
#                     message = f"Вы прекратили следить за {link}"
#                 case status.HTTP_422_UNPROCESSABLE_ENTITY:
#                     message = "Неверный формат для ссылки. Про форматы смотрите в /help"
#                 case status.HTTP_404_NOT_FOUND:
#                     message = """Ссылка не найдена. Проверьте правильность введенной ссылки.
# Список имеющихся ссылок можно посмотреть в /list"""
#                 case _:
#                     message = f"{response.text}"

#             logger.debug(f"message {message}")
#             await send_message_from_bot(event, message)


# async def list_cmd_handler(
#     event: NewMessage.Event,
# ) -> None:

#     if event.chat_id in user_states:
#         del user_states[event.chat_id]

#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             url=api_settings.url_server + "/links",
#             headers={"tg-chat-id": str(event.chat_id)},
#         )
#         if response.status_code == status.HTTP_200_OK:
#             list_link_response = ListLinksResponse.model_validate_json(response.text)
#             if not list_link_response.links:
#                 message = "Список ссылок пуст"
#             else:
#                 message = "\n".join(
#                     [
#                         f"Url: {link.link}\nTags: {link.tags}\nFilters: {link.filters}\n"
#                         for link in list_link_response.links
#                     ],
#                 )
#         elif response.status_code == status.HTTP_401_UNAUTHORIZED:
#             message = "Чат не зарегистрирован, для регистрации введите /start"
#         elif response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
#             message = f"Ошибка сервера:\n{response.text}"
#         else:
#             message = "Неизвестная ошибка"
#     await send_message_from_bot(event, message)


# async def is_chat_registrated(event: NewMessage.Event) -> bool:
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             url=api_settings.url_server + f"/tg-chat/{event.chat_id}",
#         )
#         match response.status_code:
#             case status.HTTP_401_UNAUTHORIZED:
#                 message_auth = "Чат не зарегистрирован, для регистрации введите /start"
#             case status.HTTP_500_INTERNAL_SERVER_ERROR:
#                 message_auth = f"Ошибка сервера:\n{response.text}"
#             case _:
#                 message_auth = ""
#         if message_auth:
#             await send_message_from_bot(event, message_auth)
#             return False
#         return True


# async def help_cmd_handler(
#     event: NewMessage.Event,
# ) -> None:
#     if event.chat_id in user_states:
#         del user_states[event.chat_id]
#     await send_message_from_bot(
#         event,
#         """Помощь:
# /chat_id --> текущий идентификатор чата
# /start --> запустить бота
# /help --> помощь
# /untrack --> прекратить отслеживание ссылки
# /list --> список отслеживаемых ссылок
# /track --> начать отслеживание ссылки
# Поддерживаемые форматы ссылок:
# 1. https://stackoverflow.com/questions/<номер_вопроса>
# 2. https://github.com/<владелец>/<название_репозитория>
#         """,
#     )

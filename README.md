# Study_Manager_Bot


__Telegram бот для фиксации времени учебы.__

Перед запуском нужно создать файл config.by и прописать токен телграм бота в переменную token.

Бот работает на вебхуках, поэтому вашего бота нужно перевести на вебхуки. Для этого нужно:

1) Устанавить программу ngrok с [офф.сайта](https://ngrok.com/download)
2) Прописать в консоли ngrok команду ngrok http 5000
3) Скопировать ссылку из поля Forwarding в консоли и вставить ее в поле url в ссыле на перевод телеграм бота на вебхуки.
---
p.s 

Ссылка будет выглядеть как-то так:

'https://api.telegram.org/botТУТ_НАШ_ТОКЕН_ТЕЛЕГРАММ_БОТА/setwebhook?url=ТУТ_ССЫЛКА_ИЗ_КОНСОЛИ_NGROK'

эту ссылку просто запускаем в браузере
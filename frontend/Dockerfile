# Используем только nginx — билд уже готов локально
FROM nginx:alpine

# Удаляем дефолтный сайт nginx
RUN rm -rf /usr/share/nginx/html/*

# Копируем готовую сборку (dist) из локальной машины в контейнер
COPY dist /usr/share/nginx/html

# Если есть свой конфиг nginx — раскомментируй
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открываем порт
EXPOSE 80

# Запускаем nginx
CMD ["nginx", "-g", "daemon off;"]

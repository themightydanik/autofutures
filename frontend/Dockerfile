# frontend/Dockerfile

# Stage 1: build
FROM node:18-alpine AS build

WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем исходный код
COPY . .

# Сборка для production
RUN npm run build

# Stage 2: production
FROM nginx:alpine

# Копируем собранные файлы из build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Копируем конфиг nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf
# (старое монтирование через volumes в docker-compose больше не нужно)

# Открываем порт
EXPOSE 80

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]

FROM node:20-alpine AS build
# VITE_API_BASE_URL se inyecta en build-time (Vercel lo pone via dashboard;
# en docker-compose local se deja vacío y nginx proxea /api/ al backend).
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

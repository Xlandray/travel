# Development image: Vite dev server with HMR, used by docker-compose.yml.
FROM node:22-alpine AS dev

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# Production image: a real build served as static files.
#
# VITE_API_URL is read by Vite at build time and inlined into the bundle, so it
# has to be a build arg — setting it as a container environment variable at run
# time does nothing.
FROM node:22-alpine AS build

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build


FROM nginx:1.27-alpine AS prod

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

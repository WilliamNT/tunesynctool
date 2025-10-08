FROM node:24-alpine3.21 AS build
WORKDIR /app

# Install dependencies using the lockfile for reproducible builds
COPY package.json package-lock.json ./
RUN npm ci

# Copy the rest of the sources
COPY . .

# Accept Vite environment variables provided at build time
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV NODE_ENV=production

# Produce the static build
RUN npm run build

FROM nginx:1.29.1 AS runtime

# Replace the default server configuration to support client-side routing
RUN printf 'server {\n    listen 80;\n    server_name _;\n\n    root /usr/share/nginx/html;\n    index index.html;\n\n    location / {\n        try_files $uri $uri/ /index.html;\n    }\n\n    location /assets/ {\n        add_header Cache-Control "public, max-age=31536000, immutable";\n    }\n}\n' > /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

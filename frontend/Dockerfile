FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# REACT_APP_API_URL is injected at build time by Railway
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL
RUN npm run build

# Serve the static build with a lightweight server
FROM node:20-alpine
RUN npm install -g serve
COPY --from=builder /app/build /app/build
# PORT is injected at runtime by Railway
CMD serve -s /app/build -l ${PORT:-3000}

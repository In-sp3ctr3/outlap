FROM node:24-alpine
WORKDIR /app
RUN npm install -g pnpm@11.5.2
COPY package.json ./
RUN pnpm install --prod=false
COPY . .
RUN pnpm build
EXPOSE 3000

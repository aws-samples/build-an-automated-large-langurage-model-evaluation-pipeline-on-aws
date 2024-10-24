FROM node:18.20

WORKDIR /app

COPY . .

RUN npm install

RUN npm run build

EXPOSE 3000 5000

CMD ["bash", "/app/start_servers.sh"]

FROM node:lts-alpine

WORKDIR /app

# Configurer npm pour augmenter les délais d'attente (timeout)
RUN npm config set fetch-retry-maxtimeout 600000 -g && \
    npm config set fetch-retries 5 -g

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
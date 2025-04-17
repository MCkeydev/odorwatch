FROM node:20-alpine

WORKDIR /app

COPY package.json firebase-service-account.json ./
RUN npm install

COPY forward.js ./

CMD ["node", "forward.js"]


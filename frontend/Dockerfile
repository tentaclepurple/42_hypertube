# FROM node:
FROM mcr.microsoft.com/mirror/docker/library/node:20


WORKDIR /app

COPY /app/package.json /app/package-lock.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]


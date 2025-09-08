FROM node:20

WORKDIR /app

COPY /app/package.json /app/package-lock.json ./

RUN npm install

COPY . .

EXPOSE 3000

# Comando para iniciar la aplicación en modo desarrollo
CMD ["npm", "run", "dev"]


# Usamos Node.js 20 como imagen base
FROM node:20

# Definimos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos los archivos de configuración para instalar dependencias primero (optimización de caché)
COPY /app/package.json /app/package-lock.json ./

# Instalamos las dependencias del proyecto
RUN npm install

# Copiamos el resto del código de la aplicación dentro del contenedor
COPY . .

# Exponemos el puerto 3000 para acceder a la aplicación
EXPOSE 3000

# Comando para iniciar la aplicación en modo desarrollo
CMD ["npm", "run", "dev"]


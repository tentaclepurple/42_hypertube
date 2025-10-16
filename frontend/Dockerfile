FROM mcr.microsoft.com/mirror/docker/library/node:20

WORKDIR /app

COPY app/package.json app/package-lock.json ./

RUN npm install

COPY app/ .

ENV NEXT_PUBLIC_URL=http://imontero.ddns.net:8000

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
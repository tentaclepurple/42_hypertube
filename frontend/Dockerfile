# frontend/Dockerfile

FROM mcr.microsoft.com/mirror/docker/library/node:20

WORKDIR /app

COPY app/package.json app/package-lock.json ./

RUN npm install

COPY app/ .

ARG NEXT_PUBLIC_URL
ARG BACKEND_INTERNAL_URL

ENV NEXT_PUBLIC_URL=${NEXT_PUBLIC_URL}
ENV BACKEND_INTERNAL_URL=${BACKEND_INTERNAL_URL}

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
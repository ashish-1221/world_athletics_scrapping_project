FROM mcr.microsoft.com/vscode/devcontainers/python:0-3.11

# Install system packages required to build Scrapy and its dependencies (lxml, cryptography, etc.)
ENV DEBIAN_FRONTEND=noninteractive
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		build-essential \
		git \
		curl \
		wget \
		tzdata \
		ca-certificates \
		fonts-liberation \
		libatk1.0-0 \
		libatk-bridge2.0-0 \
		libcups2 \
		libdrm2 \
		libgbm1 \
		libnspr4 \
		libnss3 \
		libx11-6 \
		libx11-xcb1 \
		libxcomposite1 \
		libxdamage1 \
		libxrandr2 \
		libxss1 \
		libasound2 \
		libpangocairo-1.0-0 \
		libpango-1.0-0 \
		libgtk-3-0 \
		libjpeg-dev \
		libpng-dev \
		pkg-config \
		cargo \
		chromium \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["sleep", "infinity"]

FROM sommersoft/pyenv-pytest:latest

COPY entrypoint.sh /entrypoint.sh

# Add mysql apt repository
RUN set -ex; \
# gpg: key 5072E1F5: public key "MySQL Release Engineering <mysql-build@oss.oracle.com>" imported
	key='859BE8D7C586F538430B19C2467B942D3A79BD29'; \
	export GNUPGHOME="$(mktemp -d)"; \
	#gpg --batch --keyserver ha.pool.sks-keyservers.net --recv-keys "$key"; \
	for server in ha.pool.sks-keyservers.net \
				  hkp://p80.pool.sks-keyservers.net:80 \
				  keyserver.ubuntu.com \
				  hkp://keyserver.ubuntu.com:80 \
				  pgp.mit.edu; do \
		gpg --keyserver "$server" --recv-keys "$key" && break || echo "Trying new keyserver..."; \
	done; \
	gpg --batch --export "$key" > /etc/apt/trusted.gpg.d/mysql.gpg; \
	gpgconf --kill all; \
	rm -rf "$GNUPGHOME"; \
	apt-key list > /dev/null
RUN echo 'deb http://repo.mysql.com/apt/debian/ buster mysql-8.0' > /etc/apt/sources.list.d/mysql.list

RUN apt-get update \
	&& apt-get install -y postgresql-client mysql-client

ENTRYPOINT [ "/entrypoint.sh" ]

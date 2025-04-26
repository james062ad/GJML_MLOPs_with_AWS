# Stage 1: Certificate setup with HTTP repo workaround
FROM alpine:latest AS cert-setup

# Override repositories to use HTTP instead of HTTPS to skip SSL verification
RUN echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/main" > /etc/apk/repositories && \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/community" >> /etc/apk/repositories && \
    apk update && apk add --no-cache ca-certificates && update-ca-certificates

COPY ZscalerRootCertificate-2048-SHA256.pem /usr/local/share/ca-certificates/zscaler.crt

# Re-run after copy to add Zscaler cert
RUN update-ca-certificates

# Stage 2: Build pgvector with Zscaler cert available
FROM postgres:alpine AS builder

# Copy trusted certs
COPY --from=cert-setup /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt

RUN apk update && apk add --no-cache \
    build-base \
    git \
    postgresql-dev \
    clang \
    llvm-dev

WORKDIR /build

RUN git clone --branch v0.5.0 https://github.com/pgvector/pgvector.git && \
    cd pgvector && make && make install

# Stage 3: Final image with pgvector + Zscaler certs
FROM postgres:alpine

# Copy trusted certs and setup HTTP repositories
COPY --from=cert-setup /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
RUN echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/main" > /etc/apk/repositories && \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/community" >> /etc/apk/repositories

# Install locale packages to fix the locale warning
RUN apk update && apk add --no-cache \
    musl-locales \
    musl-locales-lang \
    tzdata

# Set default locale
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

COPY --from=builder /usr/local/lib/postgresql/ /usr/local/lib/postgresql/
COPY --from=builder /usr/local/share/postgresql/ /usr/local/share/postgresql/

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pg_isready -U ${POSTGRES_USER:-postgres} || exit 1
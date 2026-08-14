# =============================================================================
# TradeFlow AI — Nginx Dockerfile
#
# We use the official Nginx image and just replace the default config
# with our own nginx.conf
# =============================================================================

# Official Nginx image — Alpine variant (very small, ~5MB)
FROM nginx:1.25-alpine

# Remove the default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Port 80 is where Nginx listens
EXPOSE 80

# Nginx starts automatically — no CMD needed (inherited from base image)

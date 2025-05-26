# Punto de entrada para ejecución directa del paquete hestia-pppoe
# Redirige a main.py (sin CLOUDFLARE_ZONE_ID)

from main import main

if __name__ == "__main__":
    main()

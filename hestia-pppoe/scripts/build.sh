#!/bin/bash
set -e

# Configuración
APP_NAME="hestia-pppoe"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${PROJECT_ROOT}/dist/linux"
VENV_DIR="${PROJECT_ROOT}/.venv"

# Verificar parámetros de inclusión/exclusión de .env
INCLUDE_ENV=false
NO_ENV=false
if [ "$1" = "--include-env" ] || [ "$1" = "-i" ]; then
    INCLUDE_ENV=true
    echo "🔒 Incluyendo archivo .env en el paquete"
elif [ "$1" = "--no-env" ] || [ "$1" = "-n" ]; then
    NO_ENV=true
    echo "🚫 No se incluirá ningún archivo .env en el paquete ni en la salida"
fi

# Limpiar directorios de construcción
echo "🔧 Limpiando directorios de construcción..."
rm -rf "${OUTPUT_DIR}" "${VENV_DIR}" "${PROJECT_ROOT}/build"

# Crear directorio de salida
mkdir -p "${OUTPUT_DIR}"

# Copiar .env si existe y no se incluye en el paquete y no se deshabilitó
if [ -f "${PROJECT_ROOT}/.env" ] && [ "$INCLUDE_ENV" = false ] && [ "$NO_ENV" = false ]; then
    cp "${PROJECT_ROOT}/.env" "${OUTPUT_DIR}/"
    echo "📄 Archivo .env copiado a: ${OUTPUT_DIR}/.env (fuera del paquete)"
fi

# Crear y activar entorno virtual
echo -e "\n🐍 Configurando entorno virtual..."
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r "${PROJECT_ROOT}/requirements.txt" pyinstaller

# Preparar comando de PyInstaller
PYINSTALLER_CMD=(
    "pyinstaller"
    "--name" "${APP_NAME}"
    "--onefile"
    "--clean"
    "--noconfirm"
    "--distpath" "${OUTPUT_DIR}"
    "--workpath" "${PROJECT_ROOT}/build"
    "--specpath" "${PROJECT_ROOT}"
    "--hidden-import" "pkg_resources.py2_warn"
    "--hidden-import" "logging.handlers"
    "--hidden-import" "email.mime.multipart"
    "--hidden-import" "email.mime.text"
    "--hidden-import" "dotenv"
    "--hidden-import" "requests"
    "--hidden-import" "config"
    "--hidden-import" "logger"
    "--hidden-import" "cloudflare_dns"
    "--hidden-import" "hestia_cli"
    "--hidden-import" "ip_utils"
    "--hidden-import" "filter_utils"
)

# Añadir archivos al paquete
FILES=(
    "config.py"
    "logger.py"
    "cloudflare_dns.py"
    "hestia_cli.py"
    "ip_utils.py"
    "filter_utils.py"
)

for file in "${FILES[@]}"; do
    PYINSTALLER_CMD+=("--add-data" "${PROJECT_ROOT}/${file}:.")
done

# Incluir .env en el paquete si se especificó y no se deshabilitó
if [ "$INCLUDE_ENV" = true ] && [ -f "${PROJECT_ROOT}/.env" ] && [ "$NO_ENV" = false ]; then
    PYINSTALLER_CMD+=("--add-data" "${PROJECT_ROOT}/.env:.")
    echo "🔐 Archivo .env se incluirá en el paquete"
fi

# Añadir colecciones y archivo principal
PYINSTALLER_CMD+=(
    "--collect-all" "dotenv"
    "--collect-all" "requests"
    "${PROJECT_ROOT}/main.py"
)

# Ejecutar PyInstaller
echo -e "\n🚀 Creando binario para Linux..."
"${PYINSTALLER_CMD[@]}"

# Hacer el ejecutable ejecutable
chmod +x "${OUTPUT_DIR}/${APP_NAME}"

# Mostrar mensaje de éxito
echo -e "\n✅ ¡Binario para Linux creado con éxito!"
echo "📂 Ruta: ${OUTPUT_DIR}/${APP_NAME}"

echo -e "\n📝 Instrucciones de instalación:"
echo "1. Copia el binario a tu servidor Debian:"
echo "   scp '${OUTPUT_DIR}/${APP_NAME}' usuario@tuserver:/tmp/"
echo "2. En el servidor, instala el binario:"
echo "   sudo mv /tmp/${APP_NAME} /usr/local/bin/"
echo "   sudo chmod +x /usr/local/bin/${APP_NAME}"

echo -e "\n🔧 Para usarlo como hook PPPoE:"
echo "   sudo ln -s /usr/local/bin/${APP_NAME} /etc/ppp/ip-up.d/99-hestia-update"

# Mostrar instrucciones según la opción de .env utilizada
if [ "$NO_ENV" = true ]; then
    echo -e "\n⚠️  El ejecutable se ha generado sin ningún archivo .env.\n   Deberás configurar las variables de entorno por otros medios."
elif [ "$INCLUDE_ENV" = true ]; then
    echo -e "\n✅ El archivo .env está incluido en el binario."
    echo "   No es necesario un archivo .env adicional."
else
    echo -e "\n💡 Asegúrate de que el archivo .env esté en el mismo directorio que el ejecutable"
    echo "   o en /etc/hestia-pppoe/.env"
fi

echo -e "\n📌 Uso del script:"
echo "  $0 [opciones]"
echo "  -i, --include-env   Incluir el archivo .env dentro del binario"
echo "  -n, --no-env        No incluir ni copiar ningún archivo .env (variables por otros medios)"
echo "  (sin opciones)      Mantener el archivo .env externo al binario"

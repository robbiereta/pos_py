#!/bin/bash

# Colores para los mensajes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Menú de opciones
echo -e "${GREEN}Seleccione el tipo de despliegue:${NC}"
echo "1. Despliegue local (nginx + gunicorn)"
echo "2. Despliegue a AWS Lambda"
read -p "Ingrese su elección (1-2): " choice

case $choice in
    1)
        # Ejecución del despliegue local existente
        echo -e "${GREEN}Iniciando despliegue local...${NC}"

        # Verificar si Python 3 está instalado
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv

        # Verificar si nginx está instalado
        if ! command -v nginx &> /dev/null; then
            echo -e "${RED}Nginx no está instalado. Instalando...${NC}"
            sudo apt-get install -y nginx
        fi

        # Crear entorno virtual si no existe
        if [ ! -d "venv" ]; then
            echo -e "${GREEN}Creando entorno virtual...${NC}"
            python3 -m venv venv
        fi

        # Activar entorno virtual
        echo -e "${GREEN}Activando entorno virtual...${NC}"
        source venv/bin/activate

        # Instalar dependencias
        echo -e "${GREEN}Instalando dependencias...${NC}"
        pip3 install -r requirements.txt

        # Configurar nginx
        echo -e "${GREEN}Configurando nginx...${NC}"
        sudo cp nginx/pos.conf /etc/nginx/sites-available/
        sudo ln -sf /etc/nginx/sites-available/pos.conf /etc/nginx/sites-enabled/
        sudo rm -f /etc/nginx/sites-enabled/default

        # Verificar configuración de nginx
        echo -e "${GREEN}Verificando configuración de nginx...${NC}"
        sudo nginx -t

        # Reiniciar nginx
        echo -e "${GREEN}Reiniciando nginx...${NC}"
        sudo systemctl restart nginx

        # Crear directorio para logs si no existe
        if [ ! -d "logs" ]; then
            echo -e "${GREEN}Creando directorio para logs...${NC}"
            mkdir logs
        fi

        # Crear servicio systemd para la aplicación
        echo -e "${GREEN}Configurando servicio systemd...${NC}"
        sudo tee /etc/systemd/system/pos.service << EOF
[Unit]
Description=Punto de Venta Windsurfing
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

        # Recargar systemd
        echo -e "${GREEN}Recargando systemd...${NC}"
        sudo systemctl daemon-reload

        # Iniciar y habilitar el servicio
        echo -e "${GREEN}Iniciando servicio...${NC}"
        sudo systemctl start pos
        sudo systemctl enable pos

        echo -e "${GREEN}¡Despliegue completado!${NC}"
        echo -e "${GREEN}Para ver el estado del servicio: sudo systemctl status pos${NC}"
        echo -e "${GREEN}Para ver los logs: sudo journalctl -u pos${NC}"
        ;;
    2)
        deploy_to_lambda
        ;;
    *)
        echo -e "${RED}Opción inválida${NC}"
        exit 1
        ;;
esac

# Despliegue a AWS Lambda
deploy_to_lambda() {
    echo -e "${GREEN}Preparando despliegue a AWS Lambda...${NC}"
    
    # Verificar si serverless framework está instalado
    if ! command -v serverless &> /dev/null; then
        echo -e "${RED}Serverless Framework no está instalado. Instalando...${NC}"
        npm install -g serverless
    fi
    
    # Verificar si las credenciales de AWS están configuradas
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}Credenciales de AWS no configuradas. Por favor, configure sus credenciales de AWS.${NC}"
        echo -e "${RED}Use 'aws configure' para configurar sus credenciales.${NC}"
        exit 1
    fi
    
    # Instalar dependencias de serverless
    echo -e "${GREEN}Instalando plugins de Serverless...${NC}"
    serverless plugin install -n serverless-python-requirements
    serverless plugin install -n serverless-wsgi
    
    # Realizar el despliegue
    echo -e "${GREEN}Desplegando a AWS Lambda...${NC}"
    serverless deploy --verbose
    
    echo -e "${GREEN}¡Despliegue a AWS Lambda completado!${NC}"
}

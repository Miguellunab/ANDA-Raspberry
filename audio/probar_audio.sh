#!/usr/bin/env bash

set -u

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PID_FILE="$SCRIPT_DIR/.prueba-audifonos.pid"
LOG_FILE="$SCRIPT_DIR/.prueba-audifonos.log"

esta_activo() {
    [[ -f "$PID_FILE" ]] || return 1
    local pid
    pid=$(<"$PID_FILE")
    [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null
}

activar() {
    if esta_activo; then
        echo "El sonido ya está activado (PID $(<"$PID_FILE"))."
        return 0
    fi

    rm -f "$PID_FILE"
    # En esta Raspberry Pi, la tarjeta ALSA "Headphones" es el jack de 3.5 mm.
    # Usarla directamente evita que la señal termine en alguna salida HDMI.
    nohup speaker-test -D plughw:CARD=Headphones,DEV=0 -c 2 -t sine -f 440 \
        >"$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 0.4

    if esta_activo; then
        echo "Sonido activado directamente por el jack de 3.5 mm (Headphones)."
        echo "Para detenerlo: $0 off"
    else
        echo "No se pudo iniciar el audio. Detalles:" >&2
        cat "$LOG_FILE" >&2
        rm -f "$PID_FILE"
        return 1
    fi
}

desactivar() {
    if ! esta_activo; then
        rm -f "$PID_FILE"
        echo "El sonido ya estaba desactivado."
        return 0
    fi

    local pid
    pid=$(<"$PID_FILE")
    kill "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "Sonido desactivado."
}

estado() {
    if esta_activo; then
        echo "ACTIVO (PID $(<"$PID_FILE"))"
    else
        echo "DESACTIVADO"
    fi
}

menu() {
    echo "Prueba de audífonos (jack de 3.5 mm)"
    echo "1) Activar sonido"
    echo "2) Desactivar sonido"
    echo "3) Ver estado"
    echo "q) Salir"
    read -r -p "> " opcion
    case "$opcion" in
        1) activar ;;
        2) desactivar ;;
        3) estado ;;
        q|Q) exit 0 ;;
        *) echo "Opción no válida." >&2; exit 2 ;;
    esac
}

case "${1:-menu}" in
    on|activar) activar ;;
    off|desactivar) desactivar ;;
    toggle|alternar)
        if esta_activo; then desactivar; else activar; fi
        ;;
    status|estado) estado ;;
    menu) menu ;;
    *)
        echo "Uso: $0 [on|off|toggle|status]" >&2
        exit 2
        ;;
esac

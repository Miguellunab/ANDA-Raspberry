#!/usr/bin/env python3
"""Muestra tres lineas rojas horizontales sobre un fondo negro."""

import os
import select
import sys
from pathlib import Path


# Parametros visuales para ajustar despues de la prueba con los lentes.
BACKGROUND_COLOR = (0, 0, 0)
LINE_COLOR = (255, 0, 0)
LINE_THICKNESS_RATIO = 0.10
FRAME_RATE = 30

MENU = """\
Configuraciones disponibles:
  1 - Una linea en el centro
  2 - Dos lineas, una en cada extremo
  3 - Tres lineas, extremos y centro
  q - Cerrar la prueba
"""


def configure_graphical_session():
    """Conecta una ejecucion por SSH con el escritorio Wayland local."""
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return

    runtime_dir = Path(f"/run/user/{os.getuid()}")
    wayland_socket = runtime_dir / "wayland-0"
    if not wayland_socket.exists():
        raise RuntimeError(
            "No se encontro la sesion grafica local en "
            f"{wayland_socket}. Compruebe que el escritorio este iniciado."
        )

    os.environ.setdefault("XDG_RUNTIME_DIR", str(runtime_dir))
    os.environ["WAYLAND_DISPLAY"] = wayland_socket.name


def line_positions(height, line_thickness, line_count):
    """Devuelve las posiciones superiores de las lineas solicitadas."""
    if line_count == 1:
        return ((height - line_thickness) // 2,)
    if line_count == 2:
        return (0, height - line_thickness)
    return (0, (height - line_thickness) // 2, height - line_thickness)


def draw_test_pattern(screen, pygame, line_count):
    """Dibuja el fondo y las lineas usando el tamano real de la pantalla."""
    width, height = screen.get_size()
    line_thickness = max(1, round(height * LINE_THICKNESS_RATIO))

    screen.fill(BACKGROUND_COLOR)
    for line_top in line_positions(height, line_thickness, line_count):
        pygame.draw.rect(
            screen,
            LINE_COLOR,
            (0, line_top, width, line_thickness),
        )
    pygame.display.flip()


def read_terminal_command():
    """Lee una linea de la terminal solamente cuando ya esta disponible."""
    readable, _, _ = select.select((sys.stdin,), (), (), 0)
    if not readable:
        return None

    command = sys.stdin.readline()
    if command == "":
        return "eof"
    return command.strip().lower()


def show_prompt():
    print("Seleccione una configuracion [1/2/3] o q: ", end="", flush=True)


def main():
    configure_graphical_session()

    # Se importa despues de configurar Wayland porque SDL lee estas variables
    # cuando inicializa el sistema de video.
    import pygame

    pygame.init()
    try:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Prueba de linea roja")
        pygame.mouse.set_visible(False)
        clock = pygame.time.Clock()
        line_count = 3
        terminal_input_open = True

        print("Prueba visual activa. La configuracion actual tiene 3 lineas.")
        print(MENU)
        show_prompt()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            if terminal_input_open:
                command = read_terminal_command()
                if command in ("1", "2", "3"):
                    line_count = int(command)
                    print(f"Configuracion cambiada a {line_count} linea(s).")
                    show_prompt()
                elif command == "q":
                    print("Cerrando la prueba visual...")
                    return
                elif command == "eof":
                    terminal_input_open = False
                elif command is not None:
                    print("Opcion no valida. Use 1, 2, 3 o q.")
                    show_prompt()

            draw_test_pattern(screen, pygame, line_count)
            clock.tick(FRAME_RATE)
    finally:
        pygame.mouse.set_visible(True)
        pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrueba visual detenida.")
    except (RuntimeError, OSError) as error:
        print(f"No se pudo iniciar la prueba visual: {error}", file=sys.stderr)
        raise SystemExit(1)

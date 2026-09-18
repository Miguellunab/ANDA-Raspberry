#!/usr/bin/env python3

import select
import sys

import pygame


# ==========================================================
#                  CONFIGURACION VISUAL
# ==========================================================

BACKGROUND_COLOR = (0, 0, 0)
LINE_COLOR = (255, 0, 0)

# 10 % de la altura total de la pantalla
LINE_THICKNESS_RATIO = 0.10


MENU = """\
Configuraciones disponibles:
  1 - Una linea en el centro
  2 - Dos lineas, una en cada extremo
  3 - Tres lineas, extremos y centro
  q - Cerrar la prueba
"""


# ==========================================================
#                     POSICIONES
# ==========================================================

def line_positions(height, line_thickness, line_count):

    if line_count == 1:
        return (
            (height - line_thickness) // 2,
        )

    if line_count == 2:
        return (
            0,
            height - line_thickness,
        )

    return (
        0,
        (height - line_thickness) // 2,
        height - line_thickness,
    )


# ==========================================================
#                       DIBUJO
# ==========================================================

def draw_test_pattern(screen, line_count):

    width, height = screen.get_size()

    line_thickness = max(
        1,
        round(height * LINE_THICKNESS_RATIO)
    )

    screen.fill(BACKGROUND_COLOR)

    for line_top in line_positions(
        height,
        line_thickness,
        line_count
    ):

        pygame.draw.rect(
            screen,
            LINE_COLOR,
            (
                0,
                line_top,
                width,
                line_thickness
            ),
        )

    pygame.display.flip()


# ==========================================================
#                     TERMINAL
# ==========================================================

def read_terminal_command():

    readable, _, _ = select.select(
        (sys.stdin,),
        (),
        (),
        0
    )

    if not readable:
        return None

    command = sys.stdin.readline()

    if command == "":
        return "eof"

    return command.strip().lower()


def show_prompt():

    print(
        "Seleccione una configuracion [1/2/3] o q: ",
        end="",
        flush=True
    )


# ==========================================================
#                         MAIN
# ==========================================================

def main():

    pygame.init()

    try:

        screen = pygame.display.set_mode(
            (0, 0),
            pygame.FULLSCREEN
        )

        pygame.display.set_caption(
            "ANDA - Prueba visual"
        )

        pygame.mouse.set_visible(False)

        line_count = 3
        terminal_input_open = True

        # Dibujamos una sola vez inicialmente
        draw_test_pattern(
            screen,
            line_count
        )

        print(
            "ANDA - Prueba visual activa."
        )

        print(
            f"Resolucion detectada: "
            f"{screen.get_width()} x "
            f"{screen.get_height()}"
        )

        print(
            "Configuracion inicial: 3 lineas."
        )

        print(MENU)

        show_prompt()

        running = True

        while running:

            # ---------------------------------
            # Eventos de pygame
            # ---------------------------------

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:
                        running = False

            # ---------------------------------
            # Comandos desde terminal
            # ---------------------------------

            if terminal_input_open:

                command = read_terminal_command()

                if command in ("1", "2", "3"):

                    line_count = int(command)

                    print(
                        f"\nConfiguracion cambiada a "
                        f"{line_count} linea(s)."
                    )

                    # Redibujamos SOLO cuando cambia
                    draw_test_pattern(
                        screen,
                        line_count
                    )

                    show_prompt()

                elif command == "q":

                    print(
                        "\nCerrando prueba visual..."
                    )

                    running = False

                elif command == "eof":

                    terminal_input_open = False

                elif command is not None:

                    print(
                        "\nOpcion no valida. "
                        "Use 1, 2, 3 o q."
                    )

                    show_prompt()

            # CPU casi en reposo mientras no pasa nada
            pygame.time.wait(10)

    finally:

        pygame.mouse.set_visible(True)
        pygame.quit()


if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\nPrueba visual detenida."
        )
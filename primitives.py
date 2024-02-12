import pygame
from app_settings import AppSettings
from enum import Enum

FONT = pygame.font.SysFont(AppSettings.font, AppSettings.font_size)

class Color():
    ORANGE = [255, 150, 50]
    ORANGE2 = [255, 100, 90]
    ORANGE3 = [255, 128, 128]
    WHITE = [255, 255, 255]
    BLACK = [0, 0, 0]
    GREEN = [0, 255, 0]
    BLUE = [0, 204, 255]
    LIGHTBLUE = [204, 255, 255]
    YELLOW = [255, 255, 153]
    

def render_text(text, x_pos, y_pos, color, screen):
    vertical_offset = 0
    #lines = text.splitlines()
    if not isinstance(text, list):
        text = [text]
    s = FONT.size(text[0]) #width, height
    w_max = 0
    for line in text:
        w = FONT.size(line)[0]
        w_max = w if (w > w_max) else w_max #get the max width of the lines
        lbl = FONT.render(line, True, color)
        screen.blit (lbl, (x_pos, y_pos + vertical_offset))
        vertical_offset += AppSettings.font_size #s[1]
    return ((w_max, s[1]))

def float2str(num):
    return f'{num:.1f}'

def draw_horizontal_line(surface, y_pos, color, dashcount = 0):
     width_px = surface.get_width()
     #dashcount = 40
     displacement = 0
     dashlength = width_px / dashcount
     if(dashcount > 0):
         for index in range(0, dashcount):
             pygame.draw.line(surface, color, (displacement, y_pos), (displacement + dashlength, y_pos), 1)
             displacement += dashlength * 2
     else:
         pygame.draw.line(surface, color, (0, y_pos), (dashcount, y_pos), 1)

def draw_dimline(
        surface: pygame.Surface,
        start: pygame.Vector2,
        end: pygame.Vector2,
        color: pygame.Color,
        body_width: int = 2,
        ext_width: int = 8,
        #head_height: int = 2,
    ):
    """Draw an arrow between start and end with the arrow head at the end.

    Args:
        surface (pygame.Surface): The surface to draw on
        start (pygame.Vector2): Start position
        end (pygame.Vector2): End position
        color (pygame.Color): Color of the arrow
        body_width (int, optional): Defaults to 2.
        head_width (int, optional): Defaults to 4.
        head_height (float, optional): Defaults to 2.
    """
    dimline = start - end
    angle = dimline.angle_to(pygame.Vector2(0, -1))
    body_length = dimline.length()

    # Create the triangle heads for the ends
    head_verts = [
        pygame.Vector2(0, 0),  # Center
        pygame.Vector2(ext_width / 2, 0),  # Bottomright
        #pygame.Vector2(-head_width / 2, -head_height / 2),  # Bottomleft
    ]

    tail_verts = [
        pygame.Vector2(0, 0),  # Center
        pygame.Vector2(ext_width / 2, 0),  # Bottomright
        #pygame.Vector2(-head_width / 2, -head_height / 2),  # Bottomleft
    ]

 
    # Rotate and translate the head into place
    translation = pygame.Vector2(0, dimline.length()).rotate(-angle)
    for i in range(len(head_verts)):
        head_verts[i].rotate_ip(-angle)
        head_verts[i] += translation
        head_verts[i] += start

    # Create a copy of the head and rotate 180
    translation = pygame.Vector2(0, 0).rotate(-angle)
    for i in range(len(tail_verts)):
        tail_verts[i].rotate_ip(angle + 180)
        tail_verts[i] += translation
        tail_verts[i] += start

    pygame.draw.line(surface, color, start, (start[0] - ext_width, start[1]))
    pygame.draw.line(surface, color, end, (end[0] - ext_width, end[1]))

    # Stop weird shapes when the arrow is shorter than arrow head
    if dimline.length() >= 5:
        # Calculate the body rect, rotate and translate into place
        body_verts = [
            pygame.Vector2(-body_width / 2, body_length / 2),  # Topleft
            pygame.Vector2(body_width / 2, body_length / 2),  # Topright
            pygame.Vector2(body_width / 2, -body_length / 2),  # Bottomright
            pygame.Vector2(-body_width / 2, -body_length / 2),  # Bottomleft
        ]
        translation = pygame.Vector2(0, (body_length / 2)).rotate(-angle)
        for i in range(len(body_verts)):
            body_verts[i].rotate_ip(-angle)
            body_verts[i] += translation
            body_verts[i] += start

        pygame.draw.polygon(surface, color, body_verts)
        font = pygame.font.SysFont("Arial", 36)
        
        txtsurf = font.render(str(body_length), True, color)
        surface.blit(txtsurf,(200 - txtsurf.get_width() // 2, 150 - txtsurf.get_height() // 2))

def draw_arrow(
        surface: pygame.Surface,
        start: pygame.Vector2,
        end: pygame.Vector2,
        color: pygame.Color,
        body_width: int = 2,
        head_width: int = 8,
        head_height: int = 2,
    ):
    """Draw an arrow between start and end with the arrow head at the end.

    Args:
        surface (pygame.Surface): The surface to draw on
        start (pygame.Vector2): Start position
        end (pygame.Vector2): End position
        color (pygame.Color): Color of the arrow
        body_width (int, optional): Defaults to 2.
        head_width (int, optional): Defaults to 4.
        head_height (float, optional): Defaults to 2.
    """
    arrow = start - end
    angle = arrow.angle_to(pygame.Vector2(0, -1))
    body_length = arrow.length() - (head_height * 2)

    # Create the triangle heads for the ends
    head_verts = [
        pygame.Vector2(0, head_height / 2),  # Center
        pygame.Vector2(head_width / 2, -head_height / 2),  # Bottomright
        pygame.Vector2(-head_width / 2, -head_height / 2),  # Bottomleft
    ]

    tail_verts = [
        pygame.Vector2(0, head_height / 2),  # Center
        pygame.Vector2(head_width / 2, -head_height / 2),  # Bottomright
        pygame.Vector2(-head_width / 2, -head_height / 2),  # Bottomleft
    ]

 
    # Rotate and translate the head into place
    translation = pygame.Vector2(0, arrow.length() - (head_height / 2)).rotate(-angle)
    for i in range(len(head_verts)):
        head_verts[i].rotate_ip(-angle)
        head_verts[i] += translation
        head_verts[i] += start

    # Create a copy of the head and rotate 180
    translation = pygame.Vector2(0, (head_height / 2)).rotate(-angle)
    for i in range(len(tail_verts)):
        tail_verts[i].rotate_ip(angle + 180)
        tail_verts[i] += translation
        tail_verts[i] += start

    pygame.draw.polygon(surface, color, head_verts)
    pygame.draw.polygon(surface, color, tail_verts)

    # Stop weird shapes when the arrow is shorter than arrow head
    if arrow.length() >= head_height:
        # Calculate the body rect, rotate and translate into place
        body_verts = [
            pygame.Vector2(-body_width / 2, body_length / 2),  # Topleft
            pygame.Vector2(body_width / 2, body_length / 2),  # Topright
            pygame.Vector2(body_width / 2, -body_length / 2),  # Bottomright
            pygame.Vector2(-body_width / 2, -body_length / 2),  # Bottomleft
        ]
        translation = pygame.Vector2(0, (body_length / 2) + head_height).rotate(-angle)
        for i in range(len(body_verts)):
            body_verts[i].rotate_ip(-angle)
            body_verts[i] += translation
            body_verts[i] += start

        pygame.draw.polygon(surface, color, body_verts)
        font = pygame.font.SysFont("Arial", 36)
        
        txtsurf = font.render(str(body_length), True, color)
        surface.blit(txtsurf,(200 - txtsurf.get_width() // 2, 150 - txtsurf.get_height() // 2))

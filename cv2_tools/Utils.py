# MIT License
# Copyright (c) 2019 Fernando Perez
import numpy as np
import sys
import cv2

from cv2_tools.tags_constraint import *


"""
    You can change it.
    If IGNORE_ERRORS are True, opencv_draw_tools tried to solve the problems or
    conflictive cases by himself.
    Recommended: False
"""
IGNORE_ERRORS = False


def eprint(*args, **kwargs):
    """Internal method to print into stderr"""
    if not IGNORE_ERRORS:
        print(*args, file=sys.stderr, **kwargs)


def get_lighter_color(color):
    """Generates a lighter color.

    Keyword arguments:
    color -- color you want to change, touple with 3 elements (Doesn't matter
             if it is RGB or BGR)
    Return:
    Return a lighter version of the provided color

    """
    add = 255 - max(color)
    add = min(add,30)
    return (color[0] + add, color[1] + add, color[2] + add)


def get_shape_tags(tags, font_info=(cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.75, (255,255,255), 1)):
    """Get information about how much the list of tags will occupy (width and height)
    with the current configuration.

    Arguments:
    tags -- list of strings/tags you want to check shape.

    Keyword arguments:
    font_info -- touple with 4 elements (font, font_scale, font_color, thickness)
                 font -- opencv font (default cv2.FONT_HARSHEY_COMPLEX_SMALL)
                 font_scale -- scale of the fontm between 0 and 1 (default 0.75)
                 font_color -- color of the tags text, touple with 3 elements BGR (default (255,255,255) -> white)
                          BGR = Blue - Green - Red
                 thickness -- thickness of the text in pixels (default 1)
    Return:
    Return shape of the given tags with the given font information

    """
    margin = 5
    font, font_scale, font_color, thickness = font_info

    aux_tags = []
    for tag in tags:
        line = [x+'\n' for x in tag.split('\n')]
        line[0] = line[0][:-1]
        for element in line:
            aux_tags.append(element)
    tags = aux_tags

    text_width = -1
    text_height = -1
    line_height = -1
    for tag in tags:
        size = cv2.getTextSize(tag, font, font_scale, thickness)
        text_width = max(text_width,size[0][0])
        text_height = max(text_height, size[0][1])
        line_height = max(line_height, text_height + size[1] + margin)

    return (text_width + margin * 3, (margin + text_height)*(len(tags) - 1) + 2*text_height + margin*(len(tags)-1))


def add_tags(frame, position, tags, tag_position=None, alpha=0.75, color=(20, 20, 20),
             font_info=(cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.75, (255,255,255), 1)):
    """Add tags to selected zone.

    It was originally intended as an auxiliary method to add details to the select_zone()
    method, however it can be used completely independently.

    Arguments:
    frame -- opencv frame object where you want to draw
    position -- object of type Rectangle with 4 attributes (x1, y1, x2, y2)
                This elements must be between 0 and 1 in case it is normalized
                or between 0 and frame height/width.
    tags -- list of strings/tags you want to associate to the selected zone.

    Keyword arguments:
    tag_position -- position where you want to add the tags, relatively to the selected zone (default None)
                    If None provided it will auto select the zone where it fits better:
                        - First try to put the text on the Bottom Rigth corner
                        - If it doesn't fit, try to put the text on the Bottom Left corner
                        - If it doesn't fit, try to put the text Inside the rectangle
                        - Finally if it doesn't fit, try to put the text On top of the rectangle
    alpha -- transparency of the tags background on the image (default 0.75)
             1 means totally visible and 0 totally invisible
    color -- color of the tags background, touple with 3 elements BGR (default (20,20,20) -> almost black)
             BGR = Blue - Green - Red
    font_info -- touple with 4 elements (font, font_scale, font_color, thickness)
                 font -- opencv font (default cv2.FONT_HARSHEY_COMPLEX_SMALL)
                 font_scale -- scale of the fontm between 0 and 1 (default 0.75)
                 font_color -- color of the tags text, touple with 3 elements BGR (default (255,255,255) -> white)
                          BGR = Blue - Green - Red
                 thickness -- thickness of the text in pixels (default 1)

    Return:
    A new drawed Frame

    """
    if not tags:
        return frame

    margin = 5
    f_height, f_width = frame.shape[:2]
    font, font_scale, font_color, thickness = font_info

    aux_tags = []
    for tag in tags:
        line = [x+'\n' for x in tag.split('\n')]
        line[0] = line[0][:-1]
        for element in line:
            aux_tags.append(element)
    tags = aux_tags

    text_width = -1
    text_height = -1
    line_height = -1
    for tag in tags:
        size = cv2.getTextSize(tag, font, font_scale, thickness)
        text_width = max(text_width,size[0][0])
        text_height = max(text_height, size[0][1])
        line_height = max(line_height, text_height + size[1] + margin)

    '''
        If not tags position are provided:
            - First try to put the text on the Bottom Rigth corner
            - If it doesn't fit, try to put the text on the Bottom Left corner
            - If it doesn't fit, try to put the text Inside the rectangle
            - If it doesn't fit, try to put the text On top of the rectangle
    '''
    if not tag_position:
        fits_right = position.x2 + text_width + margin*3 <= f_width
        fits_left = position.x1 - (text_width + margin*3) >= 0
        fits_below = (text_height + margin)*len(tags) - margin <= position.y2 - thickness
        fits_inside = position.x1 + text_width + margin*3 <= position.x2 - thickness and \
                      position.y1 + (margin*2 + text_height)*len(tags) + text_height - margin <= position.y2 - thickness

        if fits_right and fits_below:
            tag_position = 'bottom_right'
        elif fits_left and fits_below:
            tag_position = 'bottom_left'
        elif fits_inside:
            tag_position = 'inside'
        else:
            tag_position = 'top'
    else:
        valid = ['bottom_right', 'bottom_left', 'inside', 'top']
        if tag_position not in ['bottom_right', 'bottom_left', 'inside', 'top']:
            eprint('Warning, invalid tag_position ({}) must be in: {}'.format(tag_position, valid))
            tag_position = 'bottom_right'

    # Add triangle to know to whom each tag belongs
    if tag_position == 'bottom_right':
        pt1 = (position.x2 + margin - 1, position.y2 - (margin + text_height)*len(tags) - text_height - margin * (len(tags)-1))
        pt2 = (pt1[0], pt1[1] + text_height + margin)
        pt3 = (pt1[0] - margin + 1, pt1[1] + int(text_height/2)+margin)
    elif tag_position == 'bottom_left':
        pt1 = (position.x1 - margin + 1, position.y2 - (margin + text_height)*len(tags) - text_height - margin * (len(tags)-1))
        pt2 = (pt1[0], pt1[1] + text_height + margin)
        pt3 = (pt1[0] + margin - 1, pt1[1] + int(text_height/2)+margin)
    elif tag_position == 'top':
        pt1 = (position.x1 + margin + int(text_width/3), position.y1 - margin*2 + 1)
        pt2 = (pt1[0] + int(text_width/3) + margin*2, pt1[1])
        pt3 = (int((pt1[0] + pt2[0])/2), pt1[1] + margin*2 - 1)

    if tag_position != 'inside':
        overlay = frame.copy()
        cv2.drawContours(overlay, [np.array([pt1, pt2, pt3])], 0, color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)

    overlay = frame.copy()
    for i, tag in enumerate(tags):
        reverse_i = len(tags) - i
        extra_adjustment = 2 if tag[-1] == '\n' else 1
        if tag_position == 'top':
            cv2.rectangle(overlay, (position.x1 + margin, position.y1 - (margin + text_height)*reverse_i - margin * (reverse_i-1) - text_height - margin * (extra_adjustment - 1 )),
                          (position.x1 + text_width + margin*3, position.y1 - (margin + text_height)*reverse_i - margin * (reverse_i) + text_height), color,-1)
        elif tag_position == 'inside':
            cv2.rectangle(overlay, (position.x1 + margin, position.y1 + (margin*2 + text_height)*(i+1) + margin*i - text_height - margin * extra_adjustment),
                          (position.x1 + text_width + margin*3, position.y1 + (margin*2 + text_height)*(i+1) + margin*i + text_height - margin), color,-1)
        elif tag_position == 'bottom_left':
            cv2.rectangle(overlay, (position.x1 - (text_width + margin*3), position.y2 - (margin + text_height)*reverse_i - margin * (reverse_i-1) - text_height - margin * (extra_adjustment - 1)),
                          (position.x1 - margin, position.y2 - (margin + text_height)*reverse_i - margin * (reverse_i) + text_height), color,-1)
        elif tag_position == 'bottom_right':
            cv2.rectangle(overlay, (position.x2 + margin, position.y2 - (margin + text_height)*reverse_i - margin * (reverse_i-1) - text_height - margin * (extra_adjustment - 1)),
                          (position.x2 + text_width + margin*3, position.y2 - (margin + text_height)*reverse_i - margin * (reverse_i) + text_height), color,-1)

    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    for i, tag in enumerate(tags):
        reverse_i = len(tags) - i
        extra_adjustment = int(margin*( 0.5 if tag[-1] == '\n' else 0))
        if tag_position == 'top':
            cv2.putText(frame, tag.replace('\n',''),
                        (position.x1 + margin*2, position.y1 - (margin + text_height)*reverse_i - margin * (reverse_i-1) + int(margin/2) - extra_adjustment),
                        font, font_scale, font_color, thickness)
        elif tag_position == 'inside':
            cv2.putText(frame, tag.replace('\n',''),
                        (position.x1 + margin*2, position.y1 + (margin*2 + text_height)*(i+1) + margin*i - extra_adjustment),
                        font, font_scale, font_color, thickness)
        elif tag_position == 'bottom_left':
            cv2.putText(frame, tag.replace('\n',''),
                        (position.x1 - (text_width + margin*2), position.y2 - (margin + text_height)*reverse_i - margin * (reverse_i-1) + int(margin/2) - extra_adjustment),
                        font, font_scale, font_color, thickness)
        elif tag_position == 'bottom_right':
            cv2.putText(frame, tag.replace('\n',''),
                        (position.x2 + margin*2, position.y2 - (margin + text_height)*reverse_i - margin * (reverse_i-1) + int(margin/2) - extra_adjustment),
                        font, font_scale, font_color, thickness)

    return frame


def add_peephole(frame, position, alpha=0.5, color=(110,70,45), thickness=2, line_length=7, corners=True):
    """Add peephole effect to the select_zone.

    It was originally intended as an auxiliary method to add details to the select_zone()
    method, however it can be used completely independently.

    Position:
    frame -- opencv frame object where you want to draw
    position -- object of type Rectangle with 4 attributes (x1, y1, x2, y2)
                This elements must be between 0 and 1 in case it is normalized
                or between 0 and frame height/width.
                Outer rectangle on which the peephole is drawn.

    Keyword arguments:
    alpha -- transparency of the selected zone on the image (default 0.5)
             1 means totally visible and 0 totally invisible
    color -- color of the selected zone, touple with 3 elements BGR (default (110,70,45) -> dark blue)
             BGR = Blue - Green - Red
    normalized -- boolean parameter, if True, position provided normalized (between 0 and 1)
                  else you shold provide concrete values (default False)
    thickness -- thickness of the drawing in pixels (default 2)
    corners -- boolean parameter, if True, also draw the corners of the rectangle

    Return:
    A new drawed Frame

    """
    # Min value of thickness = 2
    thickness = min(thickness,2)
    # If the selected zone is too small don't draw
    if position.x2 - position.x1 > thickness*2 + line_length  and position.y2 - position.y1 > thickness*2 + line_length:
        overlay = frame.copy()
        if corners:
            # Draw horizontal lines of the corners
            cv2.line(overlay,(position.x1, position.y1),(position.x1 + line_length, position.y1), color, thickness+1)
            cv2.line(overlay,(position.x2, position.y1),(position.x2 - line_length, position.y1), color, thickness+1)
            cv2.line(overlay,(position.x1, position.y2),(position.x1 + line_length, position.y2), color, thickness+1)
            cv2.line(overlay,(position.x2, position.y2),(position.x2 - line_length, position.y2), color, thickness+1)
            # Draw vertical lines of the corners
            cv2.line(overlay,(position.x1, position.y1),(position.x1, position.y1 + line_length), color, thickness+1)
            cv2.line(overlay,(position.x1, position.y2),(position.x1, position.y2 - line_length), color, thickness+1)
            cv2.line(overlay,(position.x2, position.y1),(position.x2, position.y1 + line_length), color, thickness+1)
            cv2.line(overlay,(position.x2, position.y2),(position.x2, position.y2 - line_length), color, thickness+1)
        # Added extra lines that gives the peephole effect
        cv2.line(overlay,(position.x1, int((position.y1 + position.y2) / 2)),(position.x1 + line_length, int((position.y1 + position.y2) / 2)), color, thickness-1)
        cv2.line(overlay,(position.x2, int((position.y1 + position.y2) / 2)),(position.x2 - line_length, int((position.y1 + position.y2) / 2)), color, thickness-1)
        cv2.line(overlay,(int((position.x1 + position.x2) / 2), position.y1),(int((position.x1 + position.x2) / 2), position.y1 + line_length), color, thickness-1)
        cv2.line(overlay,(int((position.x1 + position.x2) / 2), position.y2),(int((position.x1 + position.x2) / 2), position.y2 - line_length), color, thickness-1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    return frame


def adjust_position(shape, position, normalized=False, thickness=0):
    """Auxiliar Method: Adjust provided position to select_zone.

    Arguments:
    shape -- touple with 2 elements (height, width)
             this information should be the height and width of the frame.
    position -- object of type Rectangle with 4 attributes (x1, y1, x2, y2)
                This elements must be between 0 and 1 in case it is normalized
                or between 0 and frame height/width.

    Keyword arguments:
    normalized -- boolean parameter, if True, position provided normalized (between 0 and 1)
                  else you shold provide concrete values (default False)
    thickness -- thickness of the drawing in pixels (default 0)

    Return:
    A new position with all the adjustments

    """
    f_height, f_width = shape
    if normalized:
        position.x1 *= f_width
        position.x2 *= f_width
        position.y1 *= f_height
        position.y2 *= f_height

    if position.x1 < 0 or position.x1 > f_width:
        eprint('Warning: x1 = {}; Value must be between {} and {}. If normalized between 0 and 1.'.format(position.x1, 0, f_width))
        position.x1 = min(max(position.x1,0),f_width)

    if position.x2 < 0 or position.x2 > f_width:
        eprint('Warning: x2 = {}; Value must be between {} and {}. If normalized between 0 and 1.'.format(position.x2, 0, f_width))
        position.x2 = min(max(position.x2,0),f_width)

    if position.y1 < 0 or position.y1 > f_height:
        eprint('Warning: y1 = {}; Value must be between {} and {}. If normalized between 0 and 1.'.format(position.y1, 0, f_height))
        position.y1 = min(max(position.y1,0),f_height)

    if position.y2 < 0 or position.y2 > f_height:
        eprint('Warning: y2 = {}; Value must be between {} and {}. If normalized between 0 and 1.'.format(position.y2, 0, f_height))
        position.y2 = min(max(position.y2,0),f_height)

    # Auto adjust the limits of the selected zone
    position.x2 = int(min(max(position.x2, thickness*2), f_width - thickness))
    position.y2 = int(min(max(position.y2, thickness*2), f_height - thickness))
    position.x1 = int(min(max(position.x1, thickness), position.x2 - thickness))
    position.y1 = int(min(max(position.y1, thickness), position.y2 - thickness))
    return position


def adjust_polygon(shape, point, normalized=False, thickness=0):
    """Auxiliar Method: Adjust provided position to select_zone.

    Arguments:
    shape -- touple with 2 elements (height, width)
             this information should be the height and width of the frame.
    point -- tuple with x and y coordinates (x1, y1)
             This elements must be between 0 and 1 in case it is normalized
             or between 0 and frame height/width.

    Keyword arguments:
    normalized -- boolean parameter, if True, position provided normalized (between 0 and 1)
                  else you shold provide concrete values (default False)
    thickness -- thickness of the drawing in pixels (default 0)

    Return:
    A new point with all the adjustments

    """
    f_height, f_width = shape
    x1, y1 = point
    if normalized:
        x1 *= f_width
        y1 *= f_height

    if x1 < 0 or x1 > f_width:
        eprint('Warning: x1 = {}; Value must be between {} and {}. If normalized between 0 and 1.'.format(x1, 0, f_width))
        x1 = min(max(x1,0),f_width)

    if y1 < 0 or y1 > f_height:
        eprint('Warning: y1 = {}; Value must be between {} and {}. If normalized between 0 and 1.'.format(y1, 0, f_height))
        y1 = min(max(y1,0),f_height)


    # Auto adjust the limits of the selected zone
    x1 = int(min(max(x1, thickness), x2 - thickness))
    y1 = int(min(max(y1, thickness), y2 - thickness))
    return (x1, y1)


def select_polygon(frame, all_vertexes, normalized=False, color=(110,70,45), thickness=2, closed=False):
    """ Draw a polygon

    Arguments:
    frame -- opencv frame object where you want to draw
    all_vertexes - List of touples (x,y) with all the vertex of the polygon

    Keyword arguments:
    normalized -- boolean parameter, if True, position provided normalized (between 0 and 1)
                  else you shold provide concrete values (default False)
    color -- color of the selected zone, touple with 3 elements BGR (default (110,70,45) -> dark blue)
             BGR = Blue - Green - Red
    thickness -- thickness of the drawing in pixels (default 0)
    closed -- boolean value, if True, it will close the polygon (the first vertex with the final one)

    Return:
    A new point with all the adjustments
    """
    if normalized:
        all_vertexes = [adjust_polygon(frame.shape[:2], vertex, normalized=True, thickness=thickness) for vertex in all_vertexes]

    for vertexes in all_vertexes:
        vertexes = np.array(vertexes)
        cv2.polylines(frame, [vertexes], closed, get_lighter_color(color), thickness=thickness-1)
    return frame


def select_zone_dict(frame, position, tags=[], tag_position=None, normalized=False, margin=5, thickness=2, other_parameters={}):
    """ Draw better rectangles to select zones.

    This is an alternative of select_zone. We use it in case we have specific
    parameters to draw this zone.

    Arguments:
    frame -- opencv frame object where you want to draw
    position -- object of type Rectangle with 4 attributes (x1, y1, x2, y2)
                This elements must be between 0 and 1 in case it is normalized
                or between 0 and frame height/width.

    Keyword arguments:
    tags -- list of strings/tags you want to associate to the selected zone (default [])
    tag_position -- position where you want to add the tags, relatively to the selected zone (default None)
                    If None provided it will auto select the zone where it fits better:
                        - First try to put the text on the Bottom Rigth corner
                        - If it doesn't fit, try to put the text on the Bottom Left corner
                        - If it doesn't fit, try to put the text Inside the rectangle
                        - Finally if it doesn't fit, try to put the text On top of the rectangle
    normalized -- boolean parameter, if True, position provided normalized (between 0 and 1)
                  else you shold provide concrete values (default False)
    margin -- extra margin in pixels to be separeted with the selected zone (default 5)
    thickness -- thickness of the drawing in pixels (default 0)
    other_parameters -- dictionary with keys alpha, color, filled and peephole
            alpha -- transparency of the selected zone on the image (default 0.9)
                     1 means totally visible and 0 totally invisible
            color -- color of the selected zone, touple with 3 elements BGR
                    (default (110,70,45) -> dark blue) BGR = Blue - Green - Red
            filled -- boolean parameter, if True, will draw a filled rectangle with
                      one-third opacity compared to the rectangle (default False)
            peephole -- boolean parameter, if True, also draw additional effect,
                        to make it looks like a peephole

    Return:
    A new point with all the adjustments
    """
    return select_zone(frame, position, tags, tag_position=tag_position,
            alpha=other_parameters['alpha'], color=other_parameters['color'],
            normalized=normalized, thickness=thickness,
            filled=other_parameters['filled'], peephole=other_parameters['peephole'],
            margin=margin)


def select_zone(frame, position, tags=[], tag_position=None, alpha=0.9, color=(110,70,45),
                normalized=False, thickness=2, filled=False, peephole=True, margin=5):
    """Draw better rectangles to select zones.

    Arguments:
    frame -- opencv frame object where you want to draw
    position -- object of type Rectangle with 4 attributes (x1, y1, x2, y2)
                This elements must be between 0 and 1 in case it is normalized
                or between 0 and frame height/width.

    Keyword arguments:
    tags -- list of strings/tags you want to associate to the selected zone (default [])
    tag_position -- position where you want to add the tags, relatively to the selected zone (default None)
                    If None provided it will auto select the zone where it fits better:
                        - First try to put the text on the Bottom Rigth corner
                        - If it doesn't fit, try to put the text on the Bottom Left corner
                        - If it doesn't fit, try to put the text Inside the rectangle
                        - Finally if it doesn't fit, try to put the text On top of the rectangle
    alpha -- transparency of the selected zone on the image (default 0.9)
             1 means totally visible and 0 totally invisible
    color -- color of the selected zone, touple with 3 elements BGR (default (110,70,45) -> dark blue)
             BGR = Blue - Green - Red
    normalized -- boolean parameter, if True, position provided normalized (between 0 and 1)
                  else you should provide concrete values (default False)
    thickness -- thickness of the drawing in pixels (default 2)
    filled -- boolean parameter, if True, will draw a filled rectangle with one-third opacity compared to the rectangle (default False)
    peephole -- boolean parameter, if True, also draw additional effect, so it looks like a peephole
    margin -- extra margin in pixels to be separeted with the selected zone (default 5)

    Return:
    A new drawed Frame

    """
    if type(position) is tuple:
        position = Rectangle(position[0],position[1],position[2],position[3])
    position = adjust_position(frame.shape[:2], position, normalized=normalized, thickness=thickness)
    if peephole:
        frame = add_peephole(frame, position, alpha=alpha, color=color)

    if filled:
        overlay = frame.copy()
        cv2.rectangle(overlay, (position.x1, position.y1), (position.x2, position.y2), color,thickness=cv2.FILLED)
        cv2.addWeighted(overlay, alpha/3.0, frame, 1 - alpha/3.0, 0, frame)

    overlay = frame.copy()
    cv2.rectangle(overlay, (position.x1, position.y1), (position.x2, position.y2), color,thickness=thickness)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    frame = add_tags(frame, position, tags, tag_position=tag_position)
    return frame


def select_multiple_zones(frame, all_selected_zones, all_tags=None, alpha=0.9, color=(110,70,45),
                normalized=False, thickness=2, filled=False, peephole=True, margin=5,
                specific_properties={}):
    """Draw better rectangles to select multiple zones at the same time.
    It will put tags to the rectangles as better as possible, avoiding (if it is possible) overwritten information.

    Arguments:
    frame -- opencv frame object where you want to draw
    all_selected_zones -- list of touple with 4 elements (x1, y1, x2, y2)
                          This elements must be between 0 and 1 in case it is normalized
                          or between 0 and frame height/width in other case.

    Keyword arguments:
    all_tags -- list of lists of strings/tags you want to associate to the selected zone.
                The first element of the list is associated with the first element of all_selected_zones.
                Therefore, both lists should have the same lenght. (default None)
    alpha -- transparency of the selected zone on the image (default 0.9)
             1 means totally visible and 0 totally invisible
    color -- color of the selected zones, touple with 3 elements BGR (default (110,70,45) -> dark blue)
             BGR = Blue - Green - Red
    normalized -- boolean parameter, if True, position provided normalized (between 0 and 1)
                  else you should provide concrete values (default False)
    thickness -- thickness of the drawing in pixels (default 2)
    filled -- boolean parameter, if True, will draw a filled rectangle with one-third opacity compared to the rectangle (default False)
    peephole -- boolean parameter, if True, also draw additional effect, so it looks like a peephole
    margin -- extra margin in pixels to be separeted with the selected zone (default 5)

    Return:
    A new drawed Frame

    """
    all_selected_zones = [adjust_position(frame.shape[:2],
                              Rectangle(zone[0],zone[1],zone[2],zone[3]),
                              normalized=normalized, thickness=thickness)
                          for zone in all_selected_zones]

    f_height, f_width = frame.shape[:2]
    all_tags_shapes = []
    best_position = []

    if all_tags:
        for i, zone in enumerate(all_selected_zones):
            all_tags_shapes.append(get_shape_tags(all_tags[i]))
        # Here you could pass the frame if you want to see where get_possible_positions
        # thinks the tags will be.           Just: frame=frame     \/
        best_position = get_possible_positions(f_width, f_height, all_selected_zones,
                        all_tags_shapes, margin=margin, frame=[])

    for i, zone in enumerate(all_selected_zones):
        tags = None
        positon = None

        # Im checking all of this stuff just in case
        if all_tags and best_position and i < len(all_tags) and i < len(best_position):
            tags = all_tags[i]
            position = best_position[i]

        if i in specific_properties:
            if 'alpha' not in specific_properties[i]:
                specific_properties[i]['alpha'] = alpha
            if 'color' not in specific_properties[i]:
                specific_properties[i]['color'] = color
            if 'filled' not in specific_properties[i]:
                specific_properties[i]['filled'] = filled
            if 'peephole' not in specific_properties[i]:
                specific_properties[i]['peephole'] = peephole

            frame = select_zone_dict(frame,zone, tags=tags,tag_position=position,
                    normalized=normalized,margin=margin, thickness=thickness,
                    other_parameters=specific_properties[i])
        else:
            frame = select_zone(frame, zone, tags=tags, tag_position=position,
                    alpha=alpha, color=color, thickness=thickness, filled=filled,
                    peephole=peephole, margin=margin)
    return frame


# TODO: Update this method or remove it
def webcam_test():
    """Reproduce Webcam in real time with a selected zone."""
    print('Launching webcam test')
    cap = cv2.VideoCapture(0)
    f_width = cap.get(3)
    f_height = cap.get(4)
    window_name = 'opencv_draw_tools'
    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        if ret:
            keystroke = cv2.waitKey(1)
            position1 = (0.33,0.25,0.66,0.85)
            tags1 = ['MIT License', '(C) Copyright\n    Fernando\n    Perez\n    Gutierrez', '@fernaperg']
            position2 = (0.12,0.41,0.3,0.9)
            tags2 = ['Release', 'v1.0.1']
            frame = select_multiple_zones(frame, [position1,position2], all_tags=[tags1,tags2], color=(14,28,200),
                                thickness=2, filled=True, normalized=True)
            cv2.imshow(window_name, frame)
            # True if escape 'esc' is pressed
            if keystroke == 27:
                break
    cv2.destroyAllWindows()
    cv2.VideoCapture(0).release()


def get_complete_help():
    return '''
    Public methods information:

    * select_zone:
    {}

    * select_multiple_zones:
    {}

    * select_zone_dict:
    {}

    * select_polygon:
    {}

    * add_peephole:
    {}

    * add_tags:
    {}

    * get_lighter_color:
    {}

    Auxiliar methods information:

    * adjust_position:
    {}

    Testing methods information:

    * webcam_test:
    {}

    '''.format(select_zone.__doc__, select_multiple_zones.__doc__, select_zone_dict.__doc__,
               select_polygon.__doc__, add_peephole.__doc__, add_tags.__doc__,
               get_lighter_color.__doc__, adjust_position.__doc__, webcam_test.__doc__)

if __name__ == '__main__':
    webcam_test()
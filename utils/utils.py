def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """
    Преобразует HEX-цвет (#RRGGBB или #RRGGBBAA) в строку формата 'rgba(r, g, b, a)'.
    alpha (0.0–1.0) используется, если в hex нет альфа-канала.
    """
    hex_color = hex_color.lstrip('#')
    
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = alpha
    elif len(hex_color) == 8:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = int(hex_color[6:8], 16) / 255
    else:
        raise ValueError("hex_color должен быть в формате #RRGGBB или #RRGGBBAA")

    return f"rgba({r}, {g}, {b}, {a:.2f})"



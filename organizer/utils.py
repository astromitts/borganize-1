color_choice_dict = {
    '------': None,
    'green': '#DAF7A6',
    'yellow': '#FFC300',
    'orange': '#FF5733',
    'red': '#C70039',
    'purple': '#581845',
}

def color_choice_tuples():
    return [(hex_value, name) for name, hex_value in color_choice_dict.items()]


def get_color_name(color_value):
    for name, hex_value in color_choice_dict.items():
        if hex_value == color_value:
            return name
    return None

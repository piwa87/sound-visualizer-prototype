"""Shared utility helpers for the sound visualizer scripts."""


def get_menu_choice(prompt: str, options: dict[int, str]) -> int:
    """Display a numbered menu and return the validated user choice.

    Keeps prompting until the user enters a valid integer key from *options*.

    Args:
        prompt: Heading to display above the list of options.
        options: Mapping of integer keys to human-readable option labels.

    Returns:
        The selected integer key.
    """
    print(f"\n     {prompt}")
    for key, label in options.items():
        print(f"     [{key}]: {label}")
    while True:
        raw = input("\n     Enter choice: ").strip()
        try:
            choice = int(raw)
            if choice in options:
                return choice
            print(f"     Please enter one of: {sorted(options)}")
        except ValueError:
            print("     Please enter a number.")

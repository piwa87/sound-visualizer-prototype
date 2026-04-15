"""Shared utility helpers for the sound visualizer scripts."""

from pathlib import Path


def choose_sound(
    choice: int,
    sounds: dict[int, tuple[str, str]],
    base_dir: Path,
) -> tuple[Path, str]:
    """Return the absolute file path and display title for the given choice.

    Args:
        choice: Integer key that must exist in *sounds*.
        sounds: Mapping of integer keys to ``(relative_path, title)`` pairs.
        base_dir: Directory that relative paths are resolved against.

    Returns:
        A ``(file_path, title)`` tuple.

    Raises:
        KeyError: If *choice* is not a valid key in *sounds*.
    """
    relative_path, title = sounds[choice]
    return base_dir / relative_path, title


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

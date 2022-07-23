import PySimpleGUIWx as sg


def main():
    menu_def = [
        "BLANK",
        ["&OpenNew§", "---", "&Save", ["1", "2", ["a", "b"]], "&Properties", "E&xit"],
    ]

    tray = sg.SystemTray(menu=menu_def, filename=r"icon.svg.png")

    while True:  # The event loop
        menu_item = tray.read()
        print(menu_item)
        if menu_item == "Exit":
            break
        elif menu_item == "OpenNew":
            sg.popup("Menu item chosen", menu_item)


if __name__ == "__main__":
    main()

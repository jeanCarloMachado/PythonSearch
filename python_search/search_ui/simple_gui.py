# !/usr/bin/env python import fire
import PySimpleGUI as sg


class Cli:
    def run(self):
        sg.Window(title="Hello World", layout=[[]], margins=(100, 50)).read()
        return "hello world"


if __name__ == "__main__":
    fire.Fire(Cli)

from PyQt5 import uic


def rename_and_move(folder_name, file_name):
    print(file_name)
    return folder_name.replace("ui/", "ui_generated/"), "ui_" + file_name

uic.compileUiDir("./src/ui/", map=rename_and_move)

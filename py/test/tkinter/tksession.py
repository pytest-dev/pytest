import py

class TkSession:
    def __init__(self, config):
        self.config = config
        
    def main(self, paths):
        import Tkinter
        root = Tkinter.Tk()
        from tkgui import TkGui 
        tkgui = TkGui(root, self.config)
        tkgui.set_paths(paths)
        root.protocol('WM_DELETE_WINDOW', tkgui.shutdown)
        root.mainloop()

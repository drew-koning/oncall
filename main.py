import logic
import wx
import wx.grid as grid
from datetime import datetime
from helper_classes import CustomGridTable


class MyApp(wx.App):
    def __init__(self):
        super().__init__(clearSigInt=True)
        logic.initializeDB()

        self.InitFrame()
    def InitFrame(self):
        self.frame = MainFrame(parent=None, title="Oncall App", pos=(100, 100))
        self.frame.Show()
        self.frame.SetSize((800, 600))
        self.frame.Center()
        self.frame.Bind(wx.EVT_CLOSE, self.OnClose) 
    def OnClose(self, event):
        """Handle the close event."""
        self.frame.Destroy()
        self.frame = None
        self.ExitMainLoop()
    
class MainFrame(wx.Frame):
    def __init__(self, parent, title, pos):
        super().__init__(parent=parent, title=title, pos=pos)
        self.panel = None
        self.show_main_view()

    def show_main_view(self):
        if self.panel:
            self.panel.DestroyLater()
        self.panel = MainPanel(self)
        self.panel.Layout()

    def show_data_view(self):
        data = logic.get_absences_from_db(datetime.today())
        if not data:
            wx.MessageBox("No data found in the database.", "Error", wx.OK | wx.ICON_ERROR)
            return
        if self.panel:
            self.panel.Destroy()
        self.panel = DataViewPanel(self, data)
        self.panel.Layout()
        self.Layout()



class MainPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # Create a sizer to manage the layout
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        # Create buttons
        load_schedule_button = wx.Button(self, label="Load Schedule")
        load_schedule_button.Bind(wx.EVT_BUTTON, self.on_load_schedule)
        show_teacher_list_button = wx.Button(self, label="Show Teacher List")
        show_teacher_list_button.Bind(wx.EVT_BUTTON, self.on_show_teacher_list)
        enter_unfilled_absences_button = wx.Button(self, label="Enter Unfilled Absences")
        enter_unfilled_absences_button.Bind(wx.EVT_BUTTON, self.on_enter_unfilled_absences)
        schedule_oncalls_button = wx.Button(self, label="Schedule Today's On Calls")
        schedule_oncalls_button.Bind(wx.EVT_BUTTON, self.schedule_oncalls)

        # Add buttons to the sizer
        hsizer.AddStretchSpacer(1)
        hsizer.Add(load_schedule_button, 0, flag=wx.EXPAND|wx.ALL , border=5)
        hsizer.Add(show_teacher_list_button, 0, flag=wx.EXPAND|wx.ALL, border=5)
        hsizer.Add(enter_unfilled_absences_button, 0,flag=wx.EXPAND|wx.ALL, border=5)
        hsizer.Add(schedule_oncalls_button, 0,flag=wx.EXPAND|wx.ALL, border=5 )
        hsizer.AddStretchSpacer(1)
        
        # Add the horizontal sizer to a vertical sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(hsizer, flag=wx.ALIGN_TOP | wx.EXPAND)

        # Set the sizer for the panel        
        self.SetSizer(sizer)
        
    
    def on_load_schedule(self, event):
        """Load the on-call schedule from the database."""
        # otherwise ask the user what new file to open
        with wx.FileDialog(self, "Open schedule file", wildcard="xlsx files (*.xlsx)|*.xlsx",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            pathname = fileDialog.GetPath()
            try:
                logic.load_schedule_from_file(pathname)
            except IOError:
                wx.LogError("Cannot open file '%s'." % pathname)
                return

    def on_show_teacher_list(self, event):
        """Show the teacher list."""
        teacher_list = logic.load_teacher_list_from_db()
        teacher_names = [teacher.name for teacher in teacher_list.get_teachers()]
        wx.MessageBox("\n".join(teacher_names), "Teacher List", wx.OK | wx.ICON_INFORMATION)

    def on_enter_unfilled_absences(self, event):
        """Enter unfilled absences for teachers."""
        data = logic.get_absences_from_db(datetime.today().strftime("%Y%m%d"))
        if not data:
            wx.MessageBox("No data found in the database.", "Error", wx.OK | wx.ICON_ERROR)
            return
        data_window = DataViewWindow(self, data)
        data_window.Show()

    def schedule_oncalls(self, event):
        pass



class DataViewWindow(wx.Frame):
    def __init__(self, parent, data):
        super().__init__(parent, title="Unfilled Absences", size=(700, 500))
        panel = DataViewPanel(self, data)
        self.Center()
        panel.AutoLayout
        

class DataViewPanel(wx.Panel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.parent = parent
        self.init_ui(data)

    def init_ui(self, data):
        """Build the dataview table and columns to display"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.data_grid = grid.Grid(self)
        self.table = CustomGridTable(data)
        self.data_grid.SetTable(self.table, takeOwnership=True)
        self.data_grid.DisableDragRowSize()
        self.data_grid.DisableDragColSize()
        self.data_grid.SetColSize(0, 0)
        self.data_grid.SetColSize(1, 150)
        self.data_grid.SetRowLabelSize(0) 
        self.data_grid.EnableEditing(False)                    # Prevents editors from showing up
        self.data_grid.SetSelectionMode(grid.Grid.GridSelectionModes.GridSelectNone) 

        for col in range(2, 7):
            self.data_grid.SetColSize(col, 60)
            self.data_grid.SetColFormatBool(col)
            for row in range(0, len(data)):
                self.data_grid.SetCellEditor(row, col, grid.GridCellBoolEditor())
                self.data_grid.SetCellRenderer(row, col, grid.GridCellBoolRenderer())
                self.data_grid.SetCellAlignment(row, col, wx.ALIGN_CENTER_HORIZONTAL, wx.ALIGN_CENTER_VERTICAL)

        for row in range(self.data_grid.GetNumberRows()):
            color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW) if row % 2 == 0 else darken_colour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW), 0.8)
            for col in range(self.data_grid.GetNumberCols()):
                self.data_grid.SetCellBackgroundColour(row, col, color)
                    # Bind click event
                self.data_grid.Bind(grid.EVT_GRID_CELL_LEFT_CLICK, self.on_cell_click)

        # Save / Cancel buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_save = wx.Button(self, label="Save")
        btn_save.Bind(wx.EVT_BUTTON, self.save)
        btn_cancel = wx.Button(self, label="Cancel")
        btn_cancel.Bind(wx.EVT_BUTTON, self.cancel)
        btn_sizer.Add(btn_save, 0, wx.RIGHT, 10)
        btn_sizer.Add(btn_cancel)

        sizer.Add(self.data_grid, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        self.SetSizer(sizer)

    def cancel(self, event):
        self.GetParent().Close()

    def save(self, event):
        response = logic.save_absences_to_db(datetime.today().strftime("%Y%m%d"), self.table.data)
        message = "Absences saved sucessfully!" if not response else "Saving failed... Try Again"
        dialog = wx.MessageDialog(self, message)
        dialog.ShowModal()
        self.cancel(event=None)

    def on_cell_click(self, event):
        row, col = event.GetRow(), event.GetCol()
        val = self.table.GetValue(row, col)
        new_val = not val
        if isinstance(val, bool):
            # Toggle value
            if col == 6:
            # Toggle all toggle columns in this row
                for toggle_col in range(2, 7):
                    self.table.SetValue(row, toggle_col, new_val)
            else:
                # Just toggle the clicked column
                self.table.SetValue(row, col, new_val)
            self.data_grid.ForceRefresh()  # Repaint the grid
        else:
            event.Skip()  # Let normal click behavior proceed


class OnCallWindow(wx.Frame):
    def __init__(self, parent, data):
        super().__init__(parent, title="Schedule On Calls", size=(700, 500))
        panel = OnCallPanel(self, data)
        self.Center()
        panel.AutoLayout

class OnCallPanel(wx.Panel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.parent = parent
        self.init_ui(data)

    def init_ui(self, data):
        pass

        



def darken_colour(colour, factor=0.9):
    """Return a darker version of the given wx.Colour."""
    r = int(colour.Red() * factor)
    g = int(colour.Green() * factor)
    b = int(colour.Blue() * factor)
    return wx.Colour(r, g, b)

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()

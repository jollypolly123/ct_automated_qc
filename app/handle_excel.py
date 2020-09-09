import openpyxl
import copy
import win32com.client
import pythoncom


def get_template():
    temp_wb = openpyxl.load_workbook("app/CT-Template.xlsx")
    return temp_wb


def input_data(workbook, information):
    data_sheet = workbook["Data"]
    data_sheet['D105'] = information['adult_abd_polyethylene']
    data_sheet['D106'] = information['adult_abd_water']
    data_sheet['D107'] = information['adult_abd_acrylic']
    data_sheet['D108'] = information['adult_abd_bone']
    data_sheet['D109'] = information['adult_abd_air']
    summary_sheet = workbook["Summary"]
    return workbook


def publish_workbook(path, path_publish):
    pythoncom.CoInitialize()

    o = win32com.client.Dispatch("Excel.Application")

    o.Visible = False

    wb_path = path

    wb = o.Workbooks.Open(wb_path)

    ws_index_list = [1, 2]  # say you want to print these sheets

    path_to_pdf = path_publish

    wb.WorkSheets(ws_index_list).Select()

    wb.ActiveSheet.ExportAsFixedFormat(0, path_to_pdf)


if __name__ == "__main__":
    # wb = get_template()
    # wb = input_data(wb, {'adult_abd_polyethylene': 130,
    #                      'adult_abd_water': 130,
    #                      'adult_abd_acrylic': 130,
    #                      'adult_abd_bone': 130,
    #                      'adult_abd_air': 130})
    # wb.save("copy.xlsx")
    path = 'C:\\Users\\jolly\\Programming\\PythonProjects\\Z&A\\proj_charon\\app\\'
    publish_workbook(path)

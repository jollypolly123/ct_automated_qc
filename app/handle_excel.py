import openpyxl
import copy
import comtypes.client
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


def publish_workbook(path, path_publish, wd_format_pdf=17):
    xlsx = comtypes.client.CreateObject("Excel.Application")
    print("Created Obj")
    wb = xlsx.Workbooks.Open(path)
    print("Opened")
    ws_index_list = [1, 2]  # say you want to print these sheets
    wb.WorkSheets(ws_index_list).Select()
    wb.ActiveSheet.ExportAsFixedFormat(0, path_publish)
    wb.Close()
    xlsx.Quit()


if __name__ == "__main__":
    path_excel = 'C:\\Users\\jolly\\Programming\\PythonProjects\\Z&A\\proj_charon\\app\\CT-Template.xlsx'
    publish_workbook(path_excel, 'C:\\Users\\jolly\\Programming\\PythonProjects\\Z&A\\proj_charon\\app\\new.pdf')

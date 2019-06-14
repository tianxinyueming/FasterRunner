import os
import xlsxwriter
import time

from FasterRunner.settings import MEDIA_ROOT


class WriteExcel(object):
    """写excel
    """
    def __init__(self, path):
        self.row = 0
        self.xl = xlsxwriter.Workbook(path)
        self.style = self.xl.add_format({'bg_color': 'green'})

    def xl_write(self, *args):
        col = 0
        style = ''
        if 'pass' in args:
            style = self.style
        for val in args:
            self.sheet.write_string(self.row, col, val, style)
            col += 1
        self.row += 1

    def log_init(self, sheetname, *title):
        self.sheet = self.xl.add_worksheet(sheetname)
        self.sheet.set_column('A:A', 20)  # 测试报告名称
        self.sheet.set_column('B:B', 10)  # 用例状态
        self.sheet.set_column('C:C', 25)  # 报错接口
        self.sheet.set_column('D:F', 60)  # traceback 请求报文，返回报文
        self.xl_write(*title)

    def log_write(self, *args):
        self.xl_write(*args)

    def xl_close(self):
        self.xl.close()


def write_excel_log(summary):
    """
    将json报告整理为简易的excel报告并存到media目录下
    """
    basepath = os.path.join(MEDIA_ROOT, 'excelReport')
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    reporttime = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(summary["time"]["start_at"]))
    reportname = reporttime + '.xlsx'
    excel_report_path = os.path.join(basepath, reportname)
    if not os.path.exists(excel_report_path):
        xinfo = WriteExcel(excel_report_path)
        xinfo.log_init('测试用例', '测试报告名称', '用例状态', '报错接口', 'traceback', '请求报文', '返回报文')
        for testcases in summary["details"]:
            error_api = testcases["records"][-1]
            error_request = error_api["meta_data"]["request"]
            error_response = error_api["meta_data"]["response"]

            testcase_status = 'pass' if testcases["success"] else 'fail'
            error_traceback = error_api["attachment"] if error_api["attachment"] else ''
            error_request_body = error_request["body"] if 'body' in error_request.keys() and error_request["body"] is not None else ''
            error_response_content = error_response["content"] if 'content' in error_response.keys() and error_response["content"] is not None else ''

            xinfo.log_write(testcases["name"], testcase_status, error_api["name"], error_traceback, error_request_body, error_response_content)
        xinfo.xl_close()

    return excel_report_path

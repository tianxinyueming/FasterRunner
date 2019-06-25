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
            if isinstance(val, list):
                for value in val:
                    self.sheet.write_string(self.row, col, value, style)
                    col += 1
            else:
                self.sheet.write_string(self.row, col, val, style)
                col += 1
        self.row += 1

    def log_init(self, sheetname, *title):
        self.sheet = self.xl.add_worksheet(sheetname)
        self.sheet.set_column('A:A', 20)  # 测试报告名称
        self.sheet.set_column('B:B', 10)  # 用例状态
        self.sheet.set_column('C:C', 25)  # 报错接口
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
        # 获取out节点下的字段字段值，进行合并，写入excel头部名
        temp_out_keys = []
        for testcases in summary["details"]:
            temp_out_keys.extend(testcases["in_out"]["out"].keys())
        out_keys = list(set(temp_out_keys))
        xinfo = WriteExcel(excel_report_path)
        xinfo.log_init('测试用例', '测试报告名称', '用例状态', '报错接口', out_keys, 'traceback', '请求报文', '返回报文')
        xinfo.log_write('name', 'status', 'error_api', out_keys, 'traceback', 'request', 'response')
        for testcases in summary["details"]:
            error_api = testcases["records"][-1]
            error_request = error_api["meta_data"]["request"]
            error_response = error_api["meta_data"]["response"]
            testcases_out = testcases["in_out"]["out"]

            testcase_status = 'pass' if testcases["success"] else 'fail'
            error_api_name = error_api["name"] if not testcases["success"] else ''
            error_traceback = error_api["attachment"] if error_api["attachment"] else ''
            error_request_body = error_request["body"] if 'body' in error_request.keys() and error_request["body"] is not None else ''
            error_response_content = error_response["content"] if 'content' in error_response.keys() and error_response["content"] is not None else ''

            out_values = [''] * len(out_keys)
            for out_key, out_value in testcases_out.items():
                if out_key in out_keys:
                    out_values[out_keys.index(out_key)] = str(out_value)

            xinfo.log_write(testcases["name"], testcase_status, error_api_name, out_values,
                            error_traceback, error_request_body, error_response_content)
        xinfo.xl_close()

    return excel_report_path
